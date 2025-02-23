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
    prompt = """
You are an expert lease analyst. Analyze the following commercial lease document and extract information into four specific sections:

1. KEY LEASE INFORMATION TABLE
Create a table with columns: Item | Paragraph Reference | Information
Include:
- Property Name
- Property Address
- Property ID/Number
- Tenant Name
- Rental Square Feet
- Amendment Type (New Lease/Renewal/Holdover/Expansion/Contraction/Remeasurement/Termination/Amendment)
- Lease Type (Office/Retail/Industrial)
- Late Fee Details (Type, Amount, Grace Period)
- Security Deposit Amount
- Lease Holdover Amount/Rate
- Tenant Contact Information (Billing, Phone, Email)
- All Dates (Effective, Commencement, Expiration)
- Suite Details (Number, Floor, Move-in/out dates, Square Feet)
Use 'N/A' if information is not found.

2. LEASE CHARGES TABLE
Create a table with columns: Charge Type | Frequency | Start Date | End Date | Amount
Include:
- All mandatory charges with specific amounts
- Charges that increase over time (show each period)
- Convert to monthly amounts where needed
- Format amounts with commas and two decimal places
Exclude conditional charges.

3. LEASE OPTIONS TABLE
Create a table with columns: Option Type | Expiration Date | Latest Notice | Earliest Notice | Notice to Tenant | Reference
Include only true legal options with predetermined terms.

4. LEASE CLAUSES TABLE
Create a table with columns: Section Title | Section Reference Number | Lease Clause
Include verbatim language for all sections and subsections.

FORMATTING RULES:
- Use commas in numbers (e.g., 1,000.00)
- Dates in MM/DD/YYYY format
- Use specified options for Amendment Type, Lease Type, Late Fee Type
- Present each section in a clearly formatted table
- Use '|' as column separator
- Start each new table with a clear header

Here is the document to analyze:

{text}

Analyze thoroughly and ensure no critical information is omitted. If any details are unclear, note that clarification may be needed.
"""
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

def parse_api_response(response_text):
    """Parse the API response into structured data"""
    try:
        # Split the response into sections
        sections = response_text.split('\n\n')
        
        tables = {
            'key_info': [],
            'charges': [],
            'options': [],
            'clauses': []
        }
        
        current_section = None
        
        for section in sections:
            if 'KEY LEASE INFORMATION' in section.upper():
                current_section = 'key_info'
            elif 'LEASE CHARGES' in section.upper():
                current_section = 'charges'
            elif 'LEASE OPTIONS' in section.upper():
                current_section = 'options'
            elif 'LEASE CLAUSES' in section.upper():
                current_section = 'clauses'
            
            if current_section and '|' in section:
                rows = [row.strip() for row in section.split('\n') if row.strip() and '|' in row]
                parsed_rows = []
                for row in rows:
                    # Skip header rows
                    if 'Item' in row and 'Reference' in row:
                        continue
                    if '---' in row:
                        continue
                        
                    cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                    if cells:
                        parsed_rows.append(cells)
                
                tables[current_section].extend(parsed_rows)
        
        return tables
    
    except Exception as e:
        print(f"Error parsing API response: {e}")
        return {
            'key_info': [],
            'charges': [],
            'options': [],
            'clauses': []
        }