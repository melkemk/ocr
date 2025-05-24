import pdfplumber
import re
from datetime import datetime
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def call_gemini_invoice_parser(raw_text, api_key):
    """
    Call the Gemini API to parse invoice text.
    Returns a dictionary of extracted data or None if there's an error.
    """
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        prompt = f"""Please extract the following information from the provided invoice text. Present the output as a single, flat JSON object. Use the exact field names as listed:
        'country', 'city', 'address', 'postal_code', 'swift_code', 'email', 'tel', 'fax', 'tin', 'vat_receipt_no', 'vat_registration_no', 'vat_registration_date' (format as YYYY-MM-DD), 'customer_name', 'region', 'sub_city', 'wereda_kebele', 'customer_vat_registration_no', 'customer_vat_registration_date' (format as YYYY-MM-DD or text if format varies), 'customer_tin', 'branch', 'payer_name', 'payer_account', 'receiver_name', 'receiver_account', 'payment_date_time' (format as YYYY-MM-DD HH:MM:SS), 'reference_no', 'service_type', 'transferred_amount' (as a number), 'commission_charge' (as a number), 'vat_on_commission' (as a number), 'total_amount' (as a number), 'amount_in_words'.
        If a field is not present or cannot be found, set its value to null.
        Here is the invoice text:

        {raw_text}"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Extract the JSON string from the response
        json_str = response.json()['candidates'][0]['content']['parts'][0]['text']
        
        # Parse the JSON string into a Python dictionary
        return json.loads(json_str)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return None

def parse_date(date_str, formats=['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']):
    """Helper function to parse dates in various formats"""
    if not date_str:
        return None
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    return None

def parse_datetime(dt_str, formats=['%Y-%m-%d %H:%M:%S', '%m/%d/%Y, %I:%M:%S %p']):
    """Helper function to parse datetimes in various formats"""
    if not dt_str:
        return None
    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue
    return None

def parse_float(value):
    """Helper function to parse float values"""
    if not value:
        return None
    try:
        if isinstance(value, str):
            return float(value.replace(',', ''))
        return float(value)
    except ValueError:
        return None

def extract_invoice_info(pdf_path):
    try:
        # Initialize data dictionary with all fields set to None
        data = {
            'country': None, 'city': None, 'address': None, 'postal_code': None,
            'swift_code': None, 'email': None, 'tel': None, 'fax': None,
            'tin': None, 'vat_receipt_no': None, 'vat_registration_no': None,
            'vat_registration_date': None,
            'customer_name': None, 'region': None, 'sub_city': None, 'wereda_kebele': None,
            'customer_vat_registration_no': None, 'customer_vat_registration_date': None,
            'customer_tin': None, 'branch': None,
            'payer_name': None, 'payer_account': None, 'receiver_name': None, 'receiver_account': None,
            'payment_date_time': None, 'reference_no': None, 'service_type': None,
            'transferred_amount': None, 'commission_charge': None, 'vat_on_commission': None,
            'total_amount': None, 'amount_in_words': None
        }

        # Extract text from PDF
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            print("Raw PDF text:", text)  # Debug: Print raw text

        # Get API key from environment
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Try Gemini API first
        ai_data = call_gemini_invoice_parser(text, api_key)
        
        if ai_data:
            # Process AI-extracted data
            for key in data.keys():
                if key in ai_data and ai_data[key] is not None:
                    if key in ['vat_registration_date', 'customer_vat_registration_date']:
                        data[key] = parse_date(ai_data[key])
                    elif key == 'payment_date_time':
                        data[key] = parse_datetime(ai_data[key])
                    elif key in ['transferred_amount', 'commission_charge', 'vat_on_commission', 'total_amount']:
                        data[key] = parse_float(ai_data[key])
                    else:
                        data[key] = ai_data[key]

        # Fallback to regex for any missing fields
        # Company Information
        company_section = re.search(r"Company Address & Other Information\n([\s\S]+?)(?:Customer Information|$)", text)
        if company_section:
            company_text = company_section.group(1)
            if data['country'] is None:
                data['country'] = re.search(r"Country:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Country:\s*([^\n]+)", company_text) else None
            if data['city'] is None:
                data['city'] = re.search(r"City:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"City:\s*([^\n]+)", company_text) else None
            if data['address'] is None:
                data['address'] = re.search(r"Address:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Address:\s*([^\n]+)", company_text) else None
            if data['postal_code'] is None:
                data['postal_code'] = re.search(r"Postal code:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Postal code:\s*([^\n]+)", company_text) else None
            if data['swift_code'] is None:
                data['swift_code'] = re.search(r"SWIFT Code:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"SWIFT Code:\s*([^\n]+)", company_text) else None
            if data['email'] is None:
                data['email'] = re.search(r"Email:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Email:\s*([^\n]+)", company_text) else None
            if data['tel'] is None:
                data['tel'] = re.search(r"Tel:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Tel:\s*([^\n]+)", company_text) else None
            if data['fax'] is None:
                data['fax'] = re.search(r"Fax:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Fax:\s*([^\n]+)", company_text) else None
            if data['tin'] is None:
                data['tin'] = re.search(r"Tin:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Tin:\s*([^\n]+)", company_text) else None
            if data['vat_receipt_no'] is None:
                data['vat_receipt_no'] = re.search(r"VAT Receipt No:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"VAT Receipt No:\s*([^\n]+)", company_text) else None
            if data['vat_registration_no'] is None:
                data['vat_registration_no'] = re.search(r"VAT Registration No:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"VAT Registration No:\s*([^\n]+)", company_text) else None
            if data['vat_registration_date'] is None:
                vat_date = re.search(r"VAT Registration Date:\s*(\d{2}/\d{2}/\d{4})", company_text)
                if vat_date:
                    data['vat_registration_date'] = parse_date(vat_date.group(1).strip())

        # Customer Information
        customer_section = re.search(r"Customer Information\n([\s\S]+?)(?:Payment / Transaction Information|$)", text)
        if customer_section:
            customer_text = customer_section.group(1)
            if data['customer_name'] is None:
                data['customer_name'] = re.search(r"Customer Name:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Customer Name:\s*([^\n]+)", customer_text) else None
            if data['region'] is None:
                data['region'] = re.search(r"Region:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Region:\s*([^\n]+)", customer_text) else None
            if data['sub_city'] is None:
                data['sub_city'] = re.search(r"Sub City:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Sub City:\s*([^\n]+)", customer_text) else None
            if data['wereda_kebele'] is None:
                data['wereda_kebele'] = re.search(r"Wereda/Kebele:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Wereda/Kebele:\s*([^\n]+)", customer_text) else None
            if data['customer_vat_registration_no'] is None:
                data['customer_vat_registration_no'] = re.search(r"VAT Registration No:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"VAT Registration No:\s*([^\n]+)", customer_text) else None
            if data['customer_vat_registration_date'] is None:
                data['customer_vat_registration_date'] = re.search(r"VAT Registration Date:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"VAT Registration Date:\s*([^\n]+)", customer_text) else None
            if data['customer_tin'] is None:
                data['customer_tin'] = re.search(r"TIN \(TAX ID\):\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"TIN \(TAX ID\):\s*([^\n]+)", customer_text) else None
            if data['branch'] is None:
                data['branch'] = re.search(r"Branch:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Branch:\s*([^\n]+)", customer_text) else None

        # Payment/Transaction Information
        payment_section = re.search(r"Payment / Transaction Information\n([\s\S]+?)(?:The Bank you can always rely on|$)", text)
        if payment_section:
            payment_text = payment_section.group(1)
            if data['payer_name'] is None:
                data['payer_name'] = re.search(r"Payer\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Payer\s+([^\n]+)", payment_text) else None
            if data['payer_account'] is None:
                data['payer_account'] = re.search(r"Account\s+(1\*{4}\d+)", payment_text).group(1).strip() if re.search(r"Account\s+(1\*{4}\d+)", payment_text) else None
            if data['receiver_name'] is None:
                data['receiver_name'] = re.search(r"Receiver\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Receiver\s+([^\n]+)", payment_text) else None
            if data['receiver_account'] is None:
                data['receiver_account'] = re.search(r"Account\s+(E\*{4}\d+)", payment_text).group(1).strip() if re.search(r"Account\s+(E\*{4}\d+)", payment_text) else None
            if data['payment_date_time'] is None:
                payment_dt = re.search(r"Payment Date & Time\s+(\d{1,2}/\d{1,2}/\d{4},\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)", payment_text)
                if payment_dt:
                    data['payment_date_time'] = parse_datetime(payment_dt.group(1).strip())
            if data['reference_no'] is None:
                data['reference_no'] = re.search(r"Reference No\. \(VAT Invoice No\)\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Reference No\. \(VAT Invoice No\)\s+([^\n]+)", payment_text) else None
            if data['service_type'] is None:
                data['service_type'] = re.search(r"Reason / Type of service\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Reason / Type of service\s+([^\n]+)", payment_text) else None
            if data['transferred_amount'] is None:
                transferred = re.search(r"Transferred Amount\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                if transferred:
                    data['transferred_amount'] = parse_float(transferred.group(1))
            if data['commission_charge'] is None:
                commission = re.search(r"Commission or Service Charge\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                if commission:
                    data['commission_charge'] = parse_float(commission.group(1))
            if data['vat_on_commission'] is None:
                vat_commission = re.search(r"15% VAT on Commission\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                if vat_commission:
                    data['vat_on_commission'] = parse_float(vat_commission.group(1))
            if data['total_amount'] is None:
                total = re.search(r"Total amount debited from customers account\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                if total:
                    data['total_amount'] = parse_float(total.group(1))
            if data['amount_in_words'] is None:
                data['amount_in_words'] = re.search(r"Amount in Word\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Amount in Word\s+([^\n]+)", payment_text) else None

        return data
    except Exception as e:
        print(f"Error extracting invoice: {e}")
        return None