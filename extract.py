import os
import fitz  # PyMuPDF
import docx
import requests
import pandas as pd
from config import ANTHROPIC_API_KEY

def read_pdf(filepath):
    text = ""
    with fitz.open(filepath) as doc:
        for page in doc:
            text += page.get_text("text")
    return text

def read_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

def generate_prompt(text):
    prompt = (
        "You are an AI contract analysis assistant specializing in commercial lease agreements. "
        "Your task is to extract key contractual terms from the following document. "
        "Return the extracted information in a structured format with the following columns:\n"
        "1. Item - The contractual term (e.g., 'Rent Amount', 'Lease Duration').\n"
        "2. Paragraph Reference - The section or paragraph number (if available).\n"
        "3. Information - The extracted details.\n\n"
        "Here is the document:\n\n"
        f"{text}\n\n"
        "Extract the information accurately and ensure completeness. "
        "If any section is ambiguous, note that clarification may be needed."
    )
    return prompt

def send_to_api(prompt):
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 1000
    }
    
    try:
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        if response.status_code == 404:
            print("Check API endpoint and version")
        elif response.status_code == 401:
            print("Check API key")
        raise
    except Exception as err:
        print(f"Other error occurred: {err}")
        raise

def process_document(filepath):
    ext = filepath.rsplit(".", 1)[1].lower()
    if ext == "pdf":
        text = read_pdf(filepath)
    elif ext == "docx":
        text = read_docx(filepath)
    else:
        raise ValueError("Unsupported file type")
    
    prompt = generate_prompt(text)
    api_response = send_to_api(prompt)
    
    # Updated to match Claude 3 API response structure
    extracted_data = api_response.get("content")[0].get("text")
    return extracted_data