"""
This module provides functionalities for interacting with the Google Gemini AI model.
It includes functions for initializing the Gemini model and generating responses
based on user input, PDF content, and conversation history.
"""

import google.generativeai as genai
from typing import Dict, Any, Optional
import re
import json

# Global Gemini model instance
_gemini_model: Optional[genai.GenerativeModel] = None

def initialize_gemini(api_key: str) -> None:
    """
    Initializes the Google Gemini AI model with the provided API key.

    Args:
        api_key: The API key for Google Gemini.
    """
    global _gemini_model
    try:
        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel("gemini-2.0-flash")
        print("[Gemini] Gemini model initialized successfully.")
    except Exception as e:
        print(f"[❌ ERROR] Failed to initialize Gemini model: {e}")
        _gemini_model = None # Ensure model is None on failure

def generate_gemini_response(
    user_message: str,
    pdf_content: str,
    conversation_history_formatted: str
) -> str:
    """
    Generates a response using the Gemini AI model, incorporating various contexts.

    The response is guided by a specific persona, PDF content,
    and conversation history, and is expected to be in a structured JSON format.

    Args:
        user_message: The current message from the user.
        pdf_content: The full content of the PDF document to be used as knowledge.
        conversation_history_formatted: The formatted historical conversation with the user.

    Returns:
        A string containing the AI's response, expected to be in JSON format.
        Returns a fallback message if the model is not initialized or an error occurs.
    """
    if not _gemini_model:
        print("[❌ ERROR] Gemini model not initialized. Cannot generate response.")
        return "Sorry, the AI is not ready yet."
    
    prompt: str = f"""
[PDF Content]:
The following information is retrieved from The BAAP Company's corporate profile. Use this information to answer user queries. If the information is not directly available in the PDF, use your general knowledge.

{pdf_content}

[Persona]:
You are Diksha, a female chatbot for The BAAP Company, acting as a helpful, knowledgeable representative, and a supportive AI counselor. You are a proper, perfect, and highly multilingual AI chatbot capable of understanding and responding to a wide range of queries naturally, concisely, and **in the exact language the user is speaking** (e.g., English, Marathi, Hindi, etc.).

[Task]:
Analyze the user's query and the provided PDF content. Your primary goal is to assist the user by providing accurate and helpful information about The BAAP Company, its services, **education offerings, product full details, and contact information**, while also offering guidance and support as a counselor would. 

*   **Information Retrieval**: If the query is related to The BAAP Company's profile, services, education, products, or contact details, use the `[PDF Content]` for detailed and accurate answers.
*   **Counseling & Support**: For general queries or personal questions, respond empathetically and provide helpful, encouraging advice as a supportive AI.
*   **Dynamic Multilingual Response**: **The primary language of response is English.** **STRICTLY respond in English by default.** Only if the user explicitly switches the language in their query (e.g., asks a question in Marathi or Hindi), then respond in that specific language (Marathi or Hindi/Devnagri script). **Do not switch languages unless the user explicitly initiates it.** Ensure your responses are culturally sensitive and appropriate.
*   **Service Promotion**: Identify opportunities to naturally suggest or promote relevant BAAP Company services based on the user's needs or questions.
*   **Tone & Style**: Maintain a helpful, friendly, empathetic, proper, perfect, short, and natural conversational tone. Always be respectful, especially when referring to individuals (like the founder, "Rao sir") or discussing company matters. Avoid sounding robotic or overly formal. Respond as if you are a human counselor and helpful AI, prioritizing clarity and conciseness.
*   **Optional Button Generation**: Generate a 'button' object in your JSON response *only* if:
    1.  The user's query *explicitly asks for a phone number, email, or a website URL*.
    2.  You cannot provide a complete or satisfactory answer from the provided PDF content, and directing the user to a website would offer more comprehensive information.
    Do NOT generate buttons for general information, service promotion, or any other reason not covered by these two conditions. If a button is generated, it must have 'type' (either "phone_number" or "url"), 'label' (max 20 characters), and 'value' (the actual phone number or URL). Otherwise, do NOT include the 'button' object in your response.
*   **JSON Response Format**: Always respond in JSON format with one mandatory key: "response_text" (your actual reply to the user) and an optional key: "button" (if a button is to be included).

Example JSON format:
```json
{{
  "response_text": "You can reach us at 9876543210 for inquiries.",
  "button": {{
    "type": "phone_number",
    "label": "Call Now",
    "value": "9876543210"
  }}
}}
```

[Conversation]:
{conversation_history_formatted}
User: {user_message}
Diksha: """
    try:
        response = _gemini_model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"[❌ ERROR] Gemini content generation failed: {e}")
        return "I apologize, but I'm having trouble processing that right now. Could you please rephrase or try again later?" 

def analyze_conversation_for_intent_and_purpose(
    conversation_history_formatted: str
) -> dict[str, Optional[str]]:
    """
    Analyzes the conversation history to determine its primary intent and purpose
    using the Gemini AI model.

    Args:
        conversation_history_formatted: The formatted historical conversation with the user.

    Returns:
        A dictionary containing 'intent' and 'purpose' (both optional strings),
        extracted from Gemini's analysis. Returns default values on error.
    """
    if not _gemini_model:
        print("[❌ ERROR] Gemini model not initialized. Cannot analyze conversation.")
        return {"intent": None, "purpose": None}

    analysis_prompt: str = f"""
    Analyze the following conversation history between a user and Diksha. Your task is to identify the primary 'intent' and provide a brief 'purpose' for the conversation.

    [Allowed Intents]:
    general_info, product_info, pricing_inquiry, appointment_booking, support_request, lead_capture, portfolio_showcase, smart_recommendation, offers_inquiry, career_or_partnership

    [Conversation History]:
    {conversation_history_formatted}

    [Instructions]:
    Based on the conversation, choose the most relevant intent from the [Allowed Intents] list. If no specific intent clearly matches, use 'general_info'. Provide a concise, 1-2 sentence summary as the 'purpose'.
    Respond strictly in JSON format with two keys: "intent" and "purpose".

    Example JSON format:
    ```json
    {{
      "intent": "product_info",
      "purpose": "The user inquired about the features and benefits of a specific company product."
    }}
    ```
    """
    try:
        response = _gemini_model.generate_content(analysis_prompt)
        pure_json_text: str = ""
        match = re.search(r'```json\s*([\s\S]*?)\s*```', response.text)
        if match:
            pure_json_text = match.group(1).strip()
        else:
            pure_json_text = response.text.strip()
        
        analysis_json: dict = json.loads(pure_json_text)
        return {
            "intent": analysis_json.get("intent"),
            "purpose": analysis_json.get("purpose")
        }
    except Exception as e:
        print(f"[❌ ERROR] Gemini conversation analysis failed: {e}")
        return {"intent": None, "purpose": None} 