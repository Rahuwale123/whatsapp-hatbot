"""
This module stores configuration variables for the WhatsApp chatbot application.
It includes API keys, service endpoints, and database connection details.

NOTE: For production environments, consider using environment variables or a
secure configuration management system instead of hardcoding sensitive data.
"""

# WhatsApp Business API Configuration
VERIFY_TOKEN: str = "rahul_gemini" # Token for webhook verification with Meta
ACCESS_TOKEN: str = "EAAPcBsYBmwQBOZBwAKMemEUVXJEg576P0GUtnyu2fMeG3LstHxIZB3hUqy1s0e6AUe3ZBvD2u3iPcUjtVuPsNZBPQvcf5SJQPSCkwoWUDZAIdiueYRBSv2peUHCJZAuAAL18u6WBszlRZAGK54ZAqDUxzI6s7ecqM2Ug43SSZCHbAxtXsOFir3ZCJGs4ZBNaHH2ruOR2gZDZD" # Your WhatsApp Business API access token
PHONE_NUMBER_ID: str = "678403788693327" # Your WhatsApp Business Account's Phone Number ID

# Google Gemini API Configuration
GEMINI_API_KEY: str = "AIzaSyD9-Q11L-ZxBSs6mXbdyFtCJkHkO3__0so" # Your Google Gemini API key

# MySQL Database Configuration
MYSQL_HOST: str = "localhost"
MYSQL_USER: str = "root"
MYSQL_PASSWORD: str = "QWer12@*"
MYSQL_DATABASE: str = "baap_wpbot_customers"

# PDF Document Configuration for RAG
PDF_FILE_NAME: str = "The Baap Company (1).pdf" # Name of the PDF file used for RAG 