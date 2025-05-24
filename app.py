from flask import Flask, request, jsonify, render_template
import sqlite3
import os
import requests
from extract_invoice import extract_invoice_info
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db():
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country TEXT,
            city TEXT,
            address TEXT,
            postal_code TEXT,
            swift_code TEXT,
            email TEXT,
            tel TEXT,
            fax TEXT,
            tin TEXT,
            vat_receipt_no TEXT,
            vat_registration_no TEXT,
            vat_registration_date DATE,
            customer_name TEXT,
            region TEXT,
            sub_city TEXT,
            wereda_kebele TEXT,
            customer_vat_registration_no TEXT,
            customer_vat_registration_date DATE,
            customer_tin TEXT,
            branch TEXT,
            payer_name TEXT,
            payer_account TEXT,
            receiver_name TEXT,
            receiver_account TEXT,
            payment_date_time TIMESTAMP,
            reference_no TEXT,
            service_type TEXT,
            transferred_amount REAL,
            commission_charge REAL,
            vat_on_commission REAL,
            total_amount REAL,
            amount_in_words TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    try:
        pdf_path = None
        
        # Handle URL input
        if 'url' in request.form and request.form['url']:
            url = request.form['url']
            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'invoice.pdf')
            response = requests.get(url)
            response.raise_for_status()
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
        
        # Handle file upload
        elif 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            if file:
                filename = secure_filename(file.filename)
                pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(pdf_path)
        
        if not pdf_path:
            return jsonify({'error': 'No URL or PDF file provided'}), 400

        # Extract invoice information
        data = extract_invoice_info(pdf_path)
        if not data:
            return jsonify({'error': 'Failed to extract invoice information'}), 400

        # Save to database
        conn = sqlite3.connect('invoices.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO invoices (
                country, city, address, postal_code, swift_code, email, tel, fax,
                tin, vat_receipt_no, vat_registration_no, vat_registration_date,
                customer_name, region, sub_city, wereda_kebele,
                customer_vat_registration_no, customer_vat_registration_date,
                customer_tin, branch, payer_name, payer_account, receiver_name,
                receiver_account, payment_date_time, reference_no, service_type,
                transferred_amount, commission_charge, vat_on_commission,
                total_amount, amount_in_words
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['country'], data['city'], data['address'], data['postal_code'],
            data['swift_code'], data['email'], data['tel'], data['fax'],
            data['tin'], data['vat_receipt_no'], data['vat_registration_no'],
            data['vat_registration_date'], data['customer_name'], data['region'],
            data['sub_city'], data['wereda_kebele'], data['customer_vat_registration_no'],
            data['customer_vat_registration_date'], data['customer_tin'],
            data['branch'], data['payer_name'], data['payer_account'],
            data['receiver_name'], data['receiver_account'], data['payment_date_time'],
            data['reference_no'], data['service_type'], data['transferred_amount'],
            data['commission_charge'], data['vat_on_commission'], data['total_amount'],
            data['amount_in_words']
        ))
        conn.commit()
        conn.close()

        # Clean up the temporary PDF file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)