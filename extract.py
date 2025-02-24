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
You are an expert lease analyst. Analyze the following commercial lease document and extract information into these specific sections. Format the output EXACTLY as shown below, maintaining the exact structure and headers:

Section 1: Key Lease Information
Create a table with these EXACT columns: Item | Paragraph Reference | Information
Include these specific items:
- Property Name
- Property Address
- Property ID or Number
- Tenant Name
- Rental Square Feet of Tenant's Leased Premise
- Amendment Type
- Lease Type
- Late Fee Calculation Type
- Late Fee Amount or Rate
- Late Fee Grace Period
- Security Deposit Amount
- Lease Holdover Amount or Rate
- Tenant Billing Contact Name
- Tenant Billing Address
- Tenant Billing Address City/State/Zip
- Tenant Phone
- Tenant Fax
- Tenant E-mail
- Lease Effective Date or Execution Date
- Lease Commencement Date
- Lease Expiration Date
- Leased Suite Number
- Suite Floor Number
- Suite Move-In Date
- Suite Move-Out Date
- Suite Rentable Square Feet

Section 2: Lease Charges
Create a table with these EXACT columns: Charge Type | Frequency | Start Date | End Date | Amount
Include:
- Base Rent for each year with specific amounts
- All recurring charges (CAM, utilities, etc.)
- Format dates as MM/DD/YYYY
- Format amounts with dollar sign and commas (e.g., $1,234.56)
- Show each period separately for escalating charges

Section 3: Lease Options
Create a table with these EXACT columns: Option Type | Expiration Date | Latest Notice | Earliest Notice | Notice to Tenant | Reference
Include:
- All lease options (renewal, termination, expansion, etc.)
- Format dates as MM/DD/YYYY
- Include specific section references
- Use N/A for any missing information

FORMATTING RULES:
1. Use exact column names as specified
2. Format all dates as MM/DD/YYYY
3. Format all currency with $ and commas
4. Use N/A for missing information
5. Include paragraph/section references where available
6. Maintain consistent capitalization
7. Each section must start with the exact section header shown above

Here is the document to analyze:

{text}

Analyze thoroughly and ensure all sections are properly formatted as specified above."""
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
        "max_tokens": 4000  # Increased token limit
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

def parse_api_response(response_text):
    """Parse the API response into structured data"""
    try:
        sections = response_text.split('\n\n')
        tables = {
            'key_info': [],
            'charges': [],
            'options': [],
            'clauses': []
        }
        
        current_section = None
        headers_seen = False
        
        for section in sections:
            if 'Section 1: Key Lease Information' in section:
                current_section = 'key_info'
                headers_seen = False
            elif 'Section 2: Lease Charges' in section:
                current_section = 'charges'
                headers_seen = False
            elif 'Section 3: Lease Options' in section:
                current_section = 'options'
                headers_seen = False
            
            if current_section and '|' in section:
                rows = [row.strip() for row in section.split('\n') if row.strip() and '|' in row]
                for row in rows:
                    if not headers_seen:
                        headers_seen = True
                        continue
                    if '---' in row:  # Skip separator rows
                        continue
                        
                    cells = [cell.strip() for cell in row.split('|') if cell.strip()]
                    if cells:
                        tables[current_section].append(cells)
        
        return tables
    except Exception as e:
        print(f"Error parsing API response: {e}")
        return {
            'key_info': [],
            'charges': [],
            'options': [],
            'clauses': []
        }

def convert_to_csv(tables):
    """Convert parsed tables to CSV format"""
    csv_data = []
    
    # Section 1: Key Lease Information
    if tables['key_info']:
        csv_data.append(['Section 1: Key Lease Information'])
        csv_data.append(['Item', 'Paragraph Reference', 'Information'])
        csv_data.extend(tables['key_info'])
        csv_data.append([])  # Empty row for separation
    
    # Section 2: Lease Charges
    if tables['charges']:
        csv_data.append(['Section 2: Lease Charges'])
        csv_data.append(['Charge Type', 'Frequency', 'Start Date', 'End Date', 'Amount'])
        csv_data.extend(tables['charges'])
        csv_data.append([])
    
    # Section 3: Lease Options
    if tables['options']:
        csv_data.append(['Section 3: Lease Options'])
        csv_data.append(['Option Type', 'Expiration Date', 'Latest Notice', 'Earliest Notice', 'Notice to Tenant', 'Reference'])
        csv_data.extend(tables['options'])
    
    # Convert to CSV
    if not csv_data:
        return "No data available"
    
    df = pd.DataFrame(csv_data)
    return df.to_csv(index=False, header=False)

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
    parsed_data = parse_api_response(extracted_data)
    
    # Debug print
    print("Parsed data:", parsed_data)
    
    csv_data = convert_to_csv(parsed_data)
    return extracted_data, csv_data