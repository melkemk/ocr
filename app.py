from flask import Flask, request, render_template, jsonify
import requests
import os
import psycopg2
from extract_invoice import extract_invoice_info
import warnings
import urllib3

# Suppress InsecureRequestWarning for development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# PostgreSQL database configuration
DB_CONFIG = {
    'dbname': 'invoices_db',
    'user': 'postgres',
    'password': 'your_postgres_password',  # Replace with the password you set
    'host': 'localhost',
    'port': '5432'
}

# Function to connect to PostgreSQL
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("Connected to database:", conn.get_dsn_parameters()['dbname'])
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Function to initialize database table
def init_db():
    conn = get_db_connection()
    if conn is None:
        print("Failed to connect to database for initialization")
        return
    
    try:
        cursor = conn.cursor()
        # Drop table to ensure clean state
        cursor.execute("DROP TABLE IF EXISTS invoices;")
        cursor.execute("""
            CREATE TABLE invoices (
                id SERIAL PRIMARY KEY,
                country VARCHAR(100),
                city VARCHAR(100),
                address VARCHAR(255),
                postal_code VARCHAR(50),
                swift_code VARCHAR(50),
                email VARCHAR(100),
                tel VARCHAR(50),
                fax VARCHAR(50),
                tin VARCHAR(50),
                vat_receipt_no VARCHAR(50),
                vat_registration_no VARCHAR(50),
                vat_registration_date DATE,
                customer_name VARCHAR(255),
                region VARCHAR(100),
                sub_city VARCHAR(100),
                wereda_kebele VARCHAR(100),
                customer_vat_registration_no VARCHAR(50),
                customer_vat_registration_date VARCHAR(50),
                customer_tin VARCHAR(50),
                branch VARCHAR(100),
                payer_name VARCHAR(255),
                payer_account VARCHAR(50),
                receiver_name VARCHAR(255),
                receiver_account VARCHAR(50),
                payment_date_time TIMESTAMP,
                reference_no VARCHAR(50),
                service_type VARCHAR(100),
                transferred_amount DECIMAL(15,2),
                commission_charge DECIMAL(15,2),
                vat_on_commission DECIMAL(15,2),
                total_amount DECIMAL(15,2),
                amount_in_words TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Database table initialized successfully")
        # Verify table columns
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'invoices';")
        columns = [row[0] for row in cursor.fetchall()]
        print("Columns in invoices table:", columns)
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        cursor.close()
        conn.close()

# Function to save extracted data to PostgreSQL
def save_to_database(data):
    print("Saving data to database:", data)
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO invoices (
                country, city, address, postal_code, swift_code, email, tel, fax, tin,
                vat_receipt_no, vat_registration_no, vat_registration_date,
                customer_name, region, sub_city, wereda_kebele, customer_vat_registration_no,
                customer_vat_registration_date, customer_tin, branch,
                payer_name, payer_account, receiver_name, receiver_account, payment_date_time,
                reference_no, service_type, transferred_amount, commission_charge,
                vat_on_commission, total_amount, amount_in_words
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            """,
            (
                data['country'], data['city'], data['address'], data['postal_code'],
                data['swift_code'], data['email'], data['tel'], data['fax'], data['tin'],
                data['vat_receipt_no'], data['vat_registration_no'], data['vat_registration_date'],
                data['customer_name'], data['region'], data['sub_city'], data['wereda_kebele'],
                data['customer_vat_registration_no'], data['customer_vat_registration_date'],
                data['customer_tin'], data['branch'],
                data['payer_name'], data['payer_account'], data['receiver_name'],
                data['receiver_account'], data['payment_date_time'], data['reference_no'],
                data['service_type'], data['transferred_amount'], data['commission_charge'],
                data['vat_on_commission'], data['total_amount'], data['amount_in_words']
            )
        )
        conn.commit()
        print("Data saved to database successfully")
        return True
    except Exception as e:
        print(f"Error saving to database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_invoice', methods=['POST'])
def process_invoice():
    url = request.form.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    # Download the PDF
    pdf_path = 'invoice.pdf'
    try:
        response = requests.get(url, verify=False)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to download PDF'}), 400
        
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
        
        # Extract invoice information
        data = extract_invoice_info(pdf_path)
        
        if data:
            # Save to database
            if save_to_database(data):
                return jsonify({
                    'data': data,
                    'message': 'Invoice processed and saved successfully'
                })
            else:
                return jsonify({'error': 'Failed to save to database'}), 500
        else:
            return jsonify({'error': 'Failed to extract invoice information'}), 400
    
    except Exception as e:
        return jsonify({'error': f'Error processing invoice: {str(e)}'}), 500
    finally:
        # Clean up: remove the downloaded PDF
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

if __name__ == '__main__':
    init_db()  # Initialize database table
    app.run(debug=True)