"""
This module provides functionalities for processing PDF files.
It includes functions for extracting text content and chunking text into smaller segments.
"""

import PyPDF2
from pathlib import Path
from typing import List, Dict, Any

def extract_text_from_pdf(pdf_path: Path) -> str:
    """
    Extracts all text content from a given PDF file.

    Args:
        pdf_path: The path to the PDF file as a Path object.

    Returns:
        A string containing all extracted text from the PDF, or an empty string
        if the file is not found or an error occurs during extraction.
    """
    text: str = ""
    if not pdf_path.is_file():
        print(f"[❌ ERROR] PDF file not found at: {pdf_path}")
        return ""
    try:
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                page_text: str = page.extract_text() or "" # Ensure text is not None
                text += page_text + "\n"
    except PyPDF2.errors.PdfReadError as e:
        print(f"[❌ ERROR] Could not read PDF file (PyPDF2 Error): {e}")
        text = ""
    except Exception as e:
        print(f"[❌ ERROR] An unexpected error occurred while extracting text from PDF: {e}")
        text = ""
    return text

def chunk_text(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """
    Splits a given text into smaller chunks with a specified overlap.

    This is a basic word-based chunking strategy.

    Args:
        text: The input text to be chunked.
        chunk_size: The maximum number of words in each chunk.
        chunk_overlap: The number of words to overlap between consecutive chunks.

    Returns:
        A list of strings, where each string is a text chunk.
    """
    chunks: List[str] = []
    if not text:
        return chunks

    words: List[str] = text.split()
    i: int = 0
    while i < len(words):
        # Ensure chunk does not go beyond the end of words list
        end_index = min(i + chunk_size, len(words))
        chunk: List[str] = words[i:end_index]
        chunks.append(" ".join(chunk))
        
        # Move index for next chunk, ensuring it doesn't go negative
        i += chunk_size - chunk_overlap
        if i < 0: # Handle cases where chunk_overlap is larger than chunk_size
            i = 0

    return chunks 