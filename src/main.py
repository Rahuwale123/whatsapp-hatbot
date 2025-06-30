"""
This module contains the main Flask application for the WhatsApp chatbot.
It handles webhook verification, processes incoming messages, and interacts with
Gemini AI, using semantically retrieved PDF content as context.
"""

from flask import Flask, request, jsonify
import json
import re
from pathlib import Path
from typing import List, Any, Optional, Dict # Re-added for type hinting
from datetime import datetime, timedelta # Import for session management
from apscheduler.schedulers.background import BackgroundScheduler # For background tasks
from apscheduler.triggers.interval import IntervalTrigger # For scheduling intervals

# Import services and config
from src import whatsapp_service
from src import gemini_service
from src import pdf_service
from src import config
from src import embedding_service
from src import mysql_service # Import MySQL service

app = Flask(__name__)

# === Configuration & Service Initialization ===
# Load config values
VERIFY_TOKEN: str = config.VERIFY_TOKEN
ACCESS_TOKEN: str = config.ACCESS_TOKEN
PHONE_NUMBER_ID: str = config.PHONE_NUMBER_ID
GEMINI_API_KEY: str = config.GEMINI_API_KEY
PDF_FILE_NAME: str = config.PDF_FILE_NAME

# MySQL Configuration
MYSQL_HOST: str = config.MYSQL_HOST
MYSQL_USER: str = config.MYSQL_USER
MYSQL_PASSWORD: str = config.MYSQL_PASSWORD
MYSQL_DATABASE: str = config.MYSQL_DATABASE

# Initialize services
whatsapp_service.initialize_whatsapp_config(ACCESS_TOKEN, PHONE_NUMBER_ID)
gemini_service.initialize_gemini(GEMINI_API_KEY)
mysql_service.initialize_mysql(MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE) # Initialize MySQL

# --- Initialize Embedding Model and Load/Embed PDF Content into ChromaDB at Startup ---
embedding_service_initialized: bool = embedding_service.initialize_embedding_service() # Changed function name

if embedding_service_initialized:
    PDF_PATH: Path = Path("data") / PDF_FILE_NAME
    if PDF_PATH.is_file():
        print(f"[PDF Loader] Extracting text from {PDF_FILE_NAME}...")
        full_pdf_text: str = pdf_service.extract_text_from_pdf(PDF_PATH)
        if full_pdf_text:
            print("[PDF Loader] Chunking extracted text...")
            pdf_chunks: List[str] = pdf_service.chunk_text(full_pdf_text)
            if pdf_chunks:
                # Check if ChromaDB collection is empty before adding to avoid duplicates
                # This relies on embedding_service._chroma_collection being accessible
                if embedding_service._chroma_collection.count() == 0: # Check collection count
                    embedding_service.process_and_store_pdf_chunks(pdf_chunks) # Changed function name
                    print(f"[PDF Loader] Stored {len(pdf_chunks)} PDF chunks into ChromaDB.")
                else:
                    print(f"[ChromaDB] Collection already contains {embedding_service._chroma_collection.count()} documents. Skipping PDF chunking and storage.")
            else:
                print("[PDF Loader] No chunks generated from PDF. Semantic search will not function.")
        else:
            print(f"[❌ ERROR] Could not extract text from PDF: {PDF_PATH}. Semantic search will not function.")
    else:
        print(f"[❌ ERROR] PDF file not found at: {PDF_PATH}. Semantic search will not function.")
else:
    print("[❌ ERROR] Embedding service (model/ChromaDB) initialization failed. Semantic search will not function.")

# === Conversation History (In-memory for current session; enhance for production) ===
# Stores {user_number: {"history": list[dict[str, str]], "last_activity": datetime}}
conversation_history: dict[str, dict[str, Any]] = {}

# Define the session timeout (e.g., 5 minutes)
SESSION_TIMEOUT_MINUTES: int = 5

# === Background Scheduler for Session Management ===
def _clear_timed_out_sessions() -> None:
    """
    Background job to periodically check for timed-out user sessions,
    extract intent/purpose, update the database, and clear session history.
    """
    global conversation_history
    current_time: datetime = datetime.now()
    users_to_remove: List[str] = []

    for user_number, session_data in conversation_history.items():
        last_activity: datetime = session_data["last_activity"]
        chat_context_list: List[Dict[str, str]] = session_data["history"]
        company_number: str = session_data["company_number"]

        if (current_time - last_activity) > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            print(f"[Background Session Clear] User {user_number}'s session timed out. Extracting intent/purpose and clearing history.")

            timed_out_history_formatted: str = ""
            for entry in chat_context_list:
                role: str = "User" if entry["role"] == "user" else "Diksha"
                timed_out_history_formatted += f"{role}: {entry['text']}\n"

            analysis_results = gemini_service.analyze_conversation_for_intent_and_purpose(timed_out_history_formatted)
            extracted_intent = analysis_results.get("intent")
            extracted_purpose = analysis_results.get("purpose")

            print(f"[Background Analysis] Extracted Intent: {extracted_intent}, Purpose: {extracted_purpose}")
            
            # Update MySQL with the extracted intent and purpose
            if extracted_intent or extracted_purpose:
                mysql_service.update_customer_chat_info(user_number, extracted_intent, extracted_purpose)
            
            users_to_remove.append(user_number)
    
    # Remove timed-out sessions from conversation_history after iteration
    for user_number in users_to_remove:
        del conversation_history[user_number]

scheduler = BackgroundScheduler()
scheduler.start()
scheduler.add_job(
    _clear_timed_out_sessions, 
    IntervalTrigger(seconds=30), # Run every 30 seconds to check for timeouts
    id='session_cleanup_job', 
    name='Session Cleanup',
    replace_existing=True
)

@app.route("/webhook", methods=["GET", "POST"])
def whatsapp_webhook() -> tuple[str, int]:
    """
    Handles incoming WhatsApp webhook requests for verification and messages.
    """
    if request.method == "GET":
        # Meta webhook verification
        token: str = request.args.get("hub.verify_token", "")
        challenge: str = request.args.get("hub.challenge", "")
        if token == VERIFY_TOKEN:
            return challenge, 200
        return "Invalid verification token", 403

    if request.method == "POST":
        data: dict = request.get_json()
        print("Incoming webhook data:", data) # Keep for initial debugging, can be removed later

        try:
            # Extract messages from the complex webhook payload structure
            messages = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('messages', [])
            
            if not messages:
                print("[INFO] No messages found in webhook data (likely status update).")
                return "ok", 200 # Acknowledge and exit for non-message events

            msg: dict = messages[0]
            
            # Process only text messages for now
            if msg.get('type') == 'text':
                user_message: str = msg.get('text', {}).get('body', '')
                user_number: str = msg.get('from', '')

                # Extract profile name from contacts if available
                profile_name: str = ""
                contacts = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('contacts', [])
                if contacts and len(contacts) > 0:
                    profile_name = contacts[0].get('profile', {}).get('name', '')
                
                # Extract the company's phone number (the recipient of the message)
                company_number: str = data.get('entry', [{}])[0].get('changes', [{}])[0].get('value', {}).get('metadata', {}).get('display_phone_number', '')

                # --- Store user in MySQL if not already present ---
                existing_customer = mysql_service.get_customer(user_number)
                if not existing_customer:
                    print(f"[MySQL] New user detected: {user_number}. Adding to database...")
                    mysql_service.add_new_customer(company_number, user_number, profile_name) # Pass company_number
                else:
                    print(f"[MySQL] User {user_number} (Display Name: {profile_name}) already exists in DB.")

                print(f"[📩] Message from {user_number} (Display Name: {profile_name if profile_name else 'N/A'}): {user_message[:50]}...")

                # Get or initialize conversation history for the user
                current_time: datetime = datetime.now()
                user_session = conversation_history.get(user_number, {"history": [], "last_activity": current_time, "company_number": company_number})
                
                # Update last activity timestamp and company number in session
                user_session["last_activity"] = current_time
                user_session["company_number"] = company_number # Ensure company_number is always up-to-date

                # Use the existing history for the current message processing
                chat_context_list = user_session["history"]

                # Add user's message to history
                chat_context_list.append({"role": "user", "text": user_message})

                # Format conversation history for Gemini prompt
                formatted_history: str = ""
                for entry in chat_context_list:
                    role: str = "User" if entry["role"] == "user" else "Diksha"
                    formatted_history += f"{role}: {entry['text']}\n"

                # --- Perform Semantic Search for Relevant PDF Chunks using ChromaDB ---
                relevant_pdf_chunks: List[str] = []
                # Check if ChromaDB collection is ready and has documents
                if embedding_service_initialized and embedding_service._chroma_collection and embedding_service._chroma_collection.count() > 0:
                    relevant_pdf_chunks = embedding_service.search_chunks(user_message, top_k=3)
                    if relevant_pdf_chunks:
                        print(f"[AI Context] Retrieved {len(relevant_pdf_chunks)} relevant PDF chunks from ChromaDB.")
                    else:
                        print("[AI Context] No relevant PDF chunks found for query in ChromaDB. AI responses may be generic.")
                else:
                    print("[AI Context] ChromaDB not ready or no PDF chunks loaded. AI responses may be generic.")
                
                # Join relevant chunks to form the context for Gemini
                pdf_ai_context: str = "\n\n".join(relevant_pdf_chunks) if relevant_pdf_chunks else ""

                # Generate response using Gemini AI
                gemini_response_text: str = gemini_service.generate_gemini_response(
                    user_message=user_message,
                    pdf_content=pdf_ai_context, # Pass only relevant PDF chunks
                    conversation_history_formatted=formatted_history
                )

                # --- Robust JSON Parsing from Gemini ---
                pure_json_text: str = ""
                match = re.search(r'```json\s*([\s\S]*?)\s*```', gemini_response_text)
                if match:
                    pure_json_text = match.group(1).strip()
                else:
                    pure_json_text = gemini_response_text.strip()
                
                final_response_text: str = ""
                try:
                    gemini_response_json: dict = json.loads(pure_json_text)
                    final_response_text = gemini_response_json.get("response_text", "")
                    action_type: str = gemini_response_json.get("action", "none")
                    print(f"[Gemini] Parsed JSON response. Action: {action_type}")

                except json.JSONDecodeError as e:
                    print(f"[❌ ERROR] Failed to decode JSON from Gemini: {e}")
                    print(f"[Gemini] Raw response: {gemini_response_text}")
                    print(f"[Gemini] Attempted to parse pure JSON: {pure_json_text}")
                    final_response_text = "Sorry, I received an unreadable response. Can you please rephrase?"
                except Exception as e:
                    print(f"[❌ ERROR] An unexpected error occurred while processing Gemini's response: {e}")
                    final_response_text = "An unexpected error occurred."

                # Add Gemini's response to history
                chat_context_list.append({"role": "Diksha", "text": final_response_text})
                # Update the user's session with the modified chat_context_list
                user_session["history"] = chat_context_list
                conversation_history[user_number] = user_session

                # Send the reply back via WhatsApp API
                whatsapp_service.send_whatsapp_message(user_number, final_response_text)
            else:
                print(f"[INFO] Received non-text message type: {msg.get('type')}")
        except KeyError as e:
            print(f"[❌ ERROR] Webhook data structure error (KeyError): {e}")
            print(f"Full webhook data: {data}")
        except TypeError as e:
            print(f"[❌ ERROR] Webhook data structure error (TypeError): {e}")
            print(f"Full webhook data: {data}")
        except Exception as e:
            print(f"[❌ ERROR] An unexpected error occurred during webhook processing: {e}")
            import traceback
            traceback.print_exc()
        return "ok", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)