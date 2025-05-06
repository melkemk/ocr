import pdfplumber
import re
from datetime import datetime

def extract_invoice_info(pdf_path):
    try:
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

        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            print("Raw PDF text:", text)  # Debug: Print raw text

            # Company Information
            company_section = re.search(r"Company Address & Other Information\n([\s\S]+?)(?:Customer Information|$)", text)
            if company_section:
                company_text = company_section.group(1)
                data['country'] = re.search(r"Country:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Country:\s*([^\n]+)", company_text) else None
                data['city'] = re.search(r"City:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"City:\s*([^\n]+)", company_text) else None
                data['address'] = re.search(r"Address:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Address:\s*([^\n]+)", company_text) else None
                data['postal_code'] = re.search(r"Postal code:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Postal code:\s*([^\n]+)", company_text) else None
                data['swift_code'] = re.search(r"SWIFT Code:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"SWIFT Code:\s*([^\n]+)", company_text) else None
                data['email'] = re.search(r"Email:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Email:\s*([^\n]+)", company_text) else None
                data['tel'] = re.search(r"Tel:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Tel:\s*([^\n]+)", company_text) else None
                data['fax'] = re.search(r"Fax:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Fax:\s*([^\n]+)", company_text) else None
                data['tin'] = re.search(r"Tin:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"Tin:\s*([^\n]+)", company_text) else None
                data['vat_receipt_no'] = re.search(r"VAT Receipt No:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"VAT Receipt No:\s*([^\n]+)", company_text) else None
                data['vat_registration_no'] = re.search(r"VAT Registration No:\s*([^\n]+)", company_text).group(1).strip() if re.search(r"VAT Registration No:\s*([^\n]+)", company_text) else None
                vat_date = re.search(r"VAT Registration Date:\s*(\d{2}/\d{2}/\d{4})", company_text)
                if vat_date:
                    try:
                        data['vat_registration_date'] = datetime.strptime(vat_date.group(1).strip(), '%d/%m/%Y').date()
                    except ValueError:
                        data['vat_registration_date'] = None

            # Customer Information
            customer_section = re.search(r"Customer Information\n([\s\S]+?)(?:Payment / Transaction Information|$)", text)
            if customer_section:
                customer_text = customer_section.group(1)
                data['customer_name'] = re.search(r"Customer Name:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Customer Name:\s*([^\n]+)", customer_text) else None
                data['region'] = re.search(r"Region:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Region:\s*([^\n]+)", customer_text) else None
                data['sub_city'] = re.search(r"Sub City:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Sub City:\s*([^\n]+)", customer_text) else None
                data['wereda_kebele'] = re.search(r"Wereda/Kebele:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Wereda/Kebele:\s*([^\n]+)", customer_text) else None
                data['customer_vat_registration_no'] = re.search(r"VAT Registration No:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"VAT Registration No:\s*([^\n]+)", customer_text) else None
                data['customer_vat_registration_date'] = re.search(r"VAT Registration Date:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"VAT Registration Date:\s*([^\n]+)", customer_text) else None
                data['customer_tin'] = re.search(r"TIN \(TAX ID\):\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"TIN \(TAX ID\):\s*([^\n]+)", customer_text) else None
                data['branch'] = re.search(r"Branch:\s*([^\n]+)", customer_text).group(1).strip() if re.search(r"Branch:\s*([^\n]+)", customer_text) else None

            # Payment/Transaction Information
            payment_section = re.search(r"Payment / Transaction Information\n([\s\S]+?)(?:The Bank you can always rely on|$)", text)
            if payment_section:
                payment_text = payment_section.group(1)
                data['payer_name'] = re.search(r"Payer\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Payer\s+([^\n]+)", payment_text) else None
                data['payer_account'] = re.search(r"Account\s+(1\*{4}\d+)", payment_text).group(1).strip() if re.search(r"Account\s+(1\*{4}\d+)", payment_text) else None
                data['receiver_name'] = re.search(r"Receiver\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Receiver\s+([^\n]+)", payment_text) else None
                data['receiver_account'] = re.search(r"Account\s+(E\*{4}\d+)", payment_text).group(1).strip() if re.search(r"Account\s+(E\*{4}\d+)", payment_text) else None
                payment_dt = re.search(r"Payment Date & Time\s+(\d{1,2}/\d{1,2}/\d{4},\s+\d{1,2}:\d{2}:\d{2}\s+[AP]M)", payment_text)
                if payment_dt:
                    try:
                        data['payment_date_time'] = datetime.strptime(payment_dt.group(1).strip(), '%m/%d/%Y, %I:%M:%S %p')
                    except ValueError:
                        data['payment_date_time'] = None
                data['reference_no'] = re.search(r"Reference No\. \(VAT Invoice No\)\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Reference No\. \(VAT Invoice No\)\s+([^\n]+)", payment_text) else None
                data['service_type'] = re.search(r"Reason / Type of service\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Reason / Type of service\s+([^\n]+)", payment_text) else None
                transferred = re.search(r"Transferred Amount\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                data['transferred_amount'] = float(transferred.group(1).replace(",", "")) if transferred else None
                commission = re.search(r"Commission or Service Charge\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                data['commission_charge'] = float(commission.group(1).replace(",", "")) if commission else None
                vat_commission = re.search(r"15% VAT on Commission\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                data['vat_on_commission'] = float(vat_commission.group(1).replace(",", "")) if vat_commission else None
                total = re.search(r"Total amount debited from customers account\s+([\d,]+\.\d{2})\s+ETB", payment_text)
                data['total_amount'] = float(total.group(1).replace(",", "")) if total else None
                data['amount_in_words'] = re.search(r"Amount in Word\s+([^\n]+)", payment_text).group(1).strip() if re.search(r"Amount in Word\s+([^\n]+)", payment_text) else None

        return data
    except Exception as e:
        print(f"Error extracting invoice: {e}")
        return None