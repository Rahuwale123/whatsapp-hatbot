# WhatsApp Gemini Chatbot with PDF Context

This is a simple WhatsApp chatbot powered by Google Gemini AI, using a PDF document as its knowledge source. The bot is designed to answer questions based on the content of "The Baap Company – Corporate Profile.pdf" and maintains a basic in-memory conversation history.

## Features

-   **WhatsApp Integration**: Receives messages via WhatsApp webhooks and sends replies.
-   **Gemini AI**: Utilizes Google Gemini's `gemini-2.0-flash` model for intelligent responses.
-   **PDF Context (RAG)**: Extracts information directly from a specified PDF file to provide relevant answers.
-   **Diksha Persona**: The bot responds as "Diksha," a helpful and knowledgeable representative of "The BAAP Company."
-   **JSON Response**: Gemini's responses are parsed from a structured JSON format.

## Setup Instructions

### 1. Prerequisites

Before you begin, ensure you have the following:

-   **Python 3.8+** installed.
-   **WhatsApp Business Account**: A Meta Developer account with a WhatsApp Business Account and a configured phone number. You'll need:
    -   A **Verify Token** (e.g., `rahul_gemini`).
    -   A **Permanent Access Token** for your WhatsApp Business Account.
    -   Your **WhatsApp Phone Number ID**.
-   **Google Gemini API Key**: Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/).

### 2. Clone the Repository

```bash
git clone <repository_url>
cd whatsapp_hatbot
```

### 3. Install Dependencies

It's highly recommended to use a virtual environment:

```bash
python -m venv venv
# On Windows
.\venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

Then, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Configuration

Open `src/config.py` and update the placeholder values with your actual API keys and IDs:

```python
# WhatsApp Business API Configuration
VERIFY_TOKEN: str = "your_whatsapp_verify_token"
ACCESS_TOKEN: str = "your_whatsapp_access_token"
PHONE_NUMBER_ID: str = "your_whatsapp_phone_number_id"

# Google Gemini API Configuration
GEMINI_API_KEY: str = "your_gemini_api_key"

# PDF Document Configuration
PDF_FILE_NAME: str = "The Baap Company – Corporate Profile.pdf" # Ensure this file is in the root directory (whatsapp_hatbot/)
```

**Important**: Make sure `The Baap Company – Corporate Profile.pdf` (or your chosen PDF) is located in the `data/` directory: `data/The Baap Company – Corporate Profile.pdf`.

### 5. Run the Application

The Flask application can be started using the `run.py` script:

```bash
# Ensure your virtual environment is active
python run.py
```

The application will run on `http://0.0.0.0:5000`.

### 6. Configure WhatsApp Webhook

1.  Go to your **Meta for Developers** dashboard.
2.  Navigate to your **WhatsApp Business Account** -> **Webhook** settings.
3.  Click "Edit" next to the Webhook URL.
4.  Set the **Callback URL** to `YOUR_PUBLIC_URL/webhook`.
    *   **Note**: For local development, you'll need a tool like `ngrok` or `localtunnel` to expose your local Flask server to the internet.
        ```bash
        # Example using ngrok (install it if you don't have it)
        ngrok http 5000
        ```
        Then, use the `https` forwarding URL provided by `ngrok` (e.g., `https://xxxxxx.ngrok.io/webhook`).
5.  Set the **Verify Token** to the same value you defined in `config.py` (e.g., `rahul_gemini`).
6.  Subscribe to the `messages` field under **Webhook Fields**.

### 7. Interact with the Chatbot

Once the webhook is configured and your Flask app is running, send a message to your WhatsApp Business number. The bot should respond based on the PDF content and its Diksha persona.

## Project Structure (Simplified)

```
whatsapp_chatbot/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main Flask application logic
│   ├── whatsapp_service.py     # Handles WhatsApp API interactions
│   ├── gemini_service.py       # Handles Gemini AI interactions
│   ├── pdf_service.py          # Handles PDF text extraction
│   └── config.py               # Stores configuration variables
├── data/
│   └── The Baap Company.pdf    # PDF document
├── .gitignore                  # Specifies intentionally untracked files to ignore
├── requirements.txt            # Lists project dependencies
└── run.py                      # Entry point to start the Flask application
``` 