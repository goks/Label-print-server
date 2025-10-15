import os
import tempfile
import json
from flask import Flask, render_template, request, jsonify
import pyodbc
import subprocess
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Global variables for database settings
DB_SERVER = os.environ.get('DB_SERVER')
DB_NAME = os.environ.get('DB_NAME')
SETTINGS_FILE = 'db_settings.json'
SELECTED_PRINTER = None  # Will store the selected printer name

def get_available_printers():
    """Get list of available printers on Windows"""
    try:
        # Use PowerShell to get printer list
        powershell_cmd = [
            'powershell', 
            '-Command', 
            'Get-Printer | Select-Object Name | ForEach-Object { $_.Name }'
        ]
        
        result = subprocess.run(powershell_cmd,
                              capture_output=True,
                              text=True,
                              timeout=10,
                              creationflags=subprocess.CREATE_NO_WINDOW)
        
        if result.returncode == 0:
            printers = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
            print(f"Server: Found {len(printers)} printers: {printers}")
            return printers
        else:
            print(f"Server: Failed to get printers: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"Server: Error getting printers: {e}")
        return []

def load_db_settings():
    """Load database settings from file or environment variables"""
    global DB_SERVER, DB_NAME, SELECTED_PRINTER
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                DB_SERVER = settings.get('server', DB_SERVER)
                DB_NAME = settings.get('database', DB_NAME)
                SELECTED_PRINTER = settings.get('printer', None)
                print(f"Server: Loaded settings - Server: {DB_SERVER}, DB: {DB_NAME}, Printer: {SELECTED_PRINTER}")
        except Exception as e:
            print(f"Error loading settings: {e}")

def save_db_settings(server, database, printer=None):
    """Save database and printer settings to file"""
    global DB_SERVER, DB_NAME, SELECTED_PRINTER
    
    try:
        settings = {
            'server': server, 
            'database': database,
            'printer': printer
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
        
        # Update global variables
        DB_SERVER = server
        DB_NAME = database
        SELECTED_PRINTER = printer
        print(f"Server: Saved settings - Server: {server}, DB: {database}, Printer: {printer}")
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# Load settings on startup
load_db_settings()

# Log startup configuration
print("="*50)
print("LABEL PRINT SERVER STARTUP")
print("="*50)
print(f"Database Server: {DB_SERVER}")
print(f"Database Name: {DB_NAME}")
if SELECTED_PRINTER:
    print(f"HARDCODED Printer: {SELECTED_PRINTER}")
    print("  → All print jobs will go to this specific printer")
else:
    print("Printer: Default System Printer")
    print("  → Will use system default printer")
print("="*50)

def get_party_info(quotation_number):
    # Format quotation number as 25-character string with 'G-' prefix, right-aligned
    formatted_vch_no = f"G-{quotation_number}".rjust(25)
    
    conn_str = (
        f"DRIVER={{SQL Server}};"
        f"SERVER={DB_SERVER};"
        f"DATABASE={DB_NAME};"
        f"Trusted_Connection=yes;"
        # f"UID={DB_USER};"
        # f"PWD={DB_PASSWORD}"
    )
    
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1: Get MasterCode from Tran2 table
        cursor.execute("SELECT CM1 FROM dbo.Tran2 WHERE VchType='26' AND VchNo=?", formatted_vch_no)
        tran_row = cursor.fetchone()
        
        if not tran_row or not tran_row.CM1:
            conn.close()
            return None
            
        master_code = tran_row.CM1
        
        # Step 2: Get shop name from Master1 table
        cursor.execute("SELECT Name, Code FROM Master1 WHERE MasterType=2 AND Code=?", master_code)
        master_row = cursor.fetchone()
        
        if not master_row:
            conn.close()
            return None
            
        shop_name = master_row.Name
        
        # Step 3: Get address information from MasterAddressInfo table
        cursor.execute("SELECT Address1, Address2, Address3, Address4, Telno, Mobile FROM MasterAddressInfo WHERE MasterCode=?", master_code)
        address_row = cursor.fetchone()
        
        conn.close()
        
        # Compile party information
        party_info = {
            'name': shop_name,
            'code': master_code,
            'address1': address_row.Address1 if address_row else '',
            'address2': address_row.Address2 if address_row else '',
            'address3': address_row.Address3 if address_row else '',
            'address4': address_row.Address4 if address_row else '',
            'phone': address_row.Telno if address_row else '',
            'mobile': address_row.Mobile if address_row else ''
        }
        
        return party_info
        
    except Exception as e:
        print(f"Database error: {e}")
        return None

def format_label(quotation, party_info):
    """Format label with crisp 5-line layout"""
    from datetime import datetime
    
    # Extract party information
    name = party_info.get('name', 'N/A')
    address_parts = [
        party_info.get('address1', ''),
        party_info.get('address2', ''),
        party_info.get('address3', ''),
        party_info.get('address4', '')
    ]
    # Clean and join address parts
    address = ', '.join([part.strip() for part in address_parts if part.strip()])
    phone = party_info.get('phone', '')
    mobile = party_info.get('mobile', '')
    
    # Crisp 5-line label format
    label_lines = []
    
    # Line 1: Quotation number
    label_lines.append(f"Q: {quotation}")
    
    # Line 2: Customer name (truncate if too long)
    customer_name = name[:45] if len(name) > 45 else name
    label_lines.append(customer_name)
    
    # Line 3: Address (truncate if too long)
    if address:
        address_line = address[:50] if len(address) > 50 else address
        label_lines.append(address_line)
    else:
        label_lines.append("")
    
    # Line 4: Contact info (phone/mobile on same line)
    contact_parts = []
    if phone:
        contact_parts.append(f"P:{phone}")
    if mobile:
        contact_parts.append(f"M:{mobile}")
    
    contact_line = " | ".join(contact_parts)
    # Truncate if too long
    contact_line = contact_line[:50] if len(contact_line) > 50 else contact_line
    label_lines.append(contact_line)
    
    # Line 5: Packed date/time
    packed_time = datetime.now().strftime('Packed: %d/%m/%Y %H:%M')
    label_lines.append(packed_time)
    
    return '\n'.join(label_lines)

def print_label(quotation, party, address='', phone='', mobile=''):
    """Print label using selected printer - runs silently on server side"""
    global SELECTED_PRINTER
    
    try:
        # Create party info dictionary for formatting
        party_info = {
            'name': party,
            'address1': address.split(',')[0].strip() if address else '',
            'address2': ','.join(address.split(',')[1:]).strip() if ',' in address else '',
            'address3': '',
            'address4': '',
            'phone': phone,
            'mobile': mobile
        }
        
        # Use the professional label formatting
        label_text = format_label(quotation, party_info)
        
        # Log which printer will be used
        printer_to_use = SELECTED_PRINTER if SELECTED_PRINTER else "Default System Printer"
        print(f"Server: Printing label for quotation {quotation}")
        print(f"Server: Target printer: {printer_to_use}")
        print(f"Label content:\n{label_text}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tf:
            tf.write(label_text)
            temp_file_name = tf.name

        # Always try PowerShell Out-Printer method first (most reliable and silent)
        try:
            if SELECTED_PRINTER:
                # Use specifically selected printer - HARDCODED until user changes it
                powershell_cmd = [
                    'powershell', 
                    '-Command', 
                    f'Get-Content "{temp_file_name}" | Out-Printer -Name "{SELECTED_PRINTER}"'
                ]
                print(f"Server: Using HARDCODED printer selection: {SELECTED_PRINTER}")
            else:
                # Use default printer only if no printer has been selected
                powershell_cmd = [
                    'powershell', 
                    '-Command', 
                    f'Get-Content "{temp_file_name}" | Out-Printer'
                ]
                print(f"Server: Using default printer (no printer selection made yet)")
            
            result = subprocess.run(powershell_cmd, 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=30,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                print(f"Server: Print job sent successfully to {printer_to_use}")
                success = True
            else:
                print(f"Server: PowerShell print failed: {result.stderr}")
                # If selected printer fails, do NOT fallback to default - user should know
                if SELECTED_PRINTER:
                    print(f"Server: HARDCODED printer '{SELECTED_PRINTER}' failed - not falling back to default")
                    success = False
                else:
                    success = False
                
        except Exception as ps_error:
            print(f"Server: PowerShell method failed: {ps_error}")
            
            # Only try fallback methods if no specific printer is selected
            # If user selected a specific printer, we should not fallback to different methods
            if not SELECTED_PRINTER:
                print("Server: Trying fallback print method (Windows print command)")
                try:
                    print_cmd = ['print', '/D:PRN', temp_file_name]
                    result = subprocess.run(print_cmd,
                                          capture_output=True,
                                          text=True,
                                          timeout=30,
                                          creationflags=subprocess.CREATE_NO_WINDOW)
                    
                    if result.returncode == 0:
                        print(f"Server: Print job sent successfully via print command")
                        success = True
                    else:
                        print(f"Server: Print command failed: {result.stderr}")
                        success = False
                        
                except Exception as print_error:
                    print(f"Server: All print methods failed: {print_error}")
                    success = False
            else:
                print(f"Server: Selected printer '{SELECTED_PRINTER}' failed - will not use fallback methods")
                success = False
        
        # Clean up temporary file
        try:
            os.unlink(temp_file_name)
        except:
            pass  # File might already be deleted
            
        return success
        
    except subprocess.TimeoutExpired:
        print("Server: Print command timed out")
        return False
    except Exception as e:
        print(f"Server: Print error: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lookup', methods=['POST'])
def lookup():
    data = request.json
    if not data:
        return jsonify({'party': None})
        
    quotation = data.get('quotation')
    party_info = get_party_info(quotation)
    
    if party_info:
        return jsonify({
            'party': party_info['name'],
            'address': f"{party_info['address1']} {party_info['address2']} {party_info['address3']} {party_info['address4']}".strip(),
            'phone': party_info['phone'],
            'mobile': party_info['mobile']
        })
    else:
        return jsonify({'party': None})

@app.route('/preview-label', methods=['POST'])
def preview_label():
    """Generate label preview without printing"""
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'})
        
    quotation = data.get('quotation')
    party = data.get('party')
    address = data.get('address', '')
    phone = data.get('phone', '')
    mobile = data.get('mobile', '')
    
    if not quotation or not party:
        return jsonify({'status': 'error', 'message': 'Quotation and party are required'})
    
    # Create party info dictionary for formatting
    party_info = {
        'name': party,
        'address1': address.split(',')[0].strip() if address else '',
        'address2': ','.join(address.split(',')[1:]).strip() if ',' in address else '',
        'address3': '',
        'address4': '',
        'phone': phone,
        'mobile': mobile
    }
    
    # Generate label preview
    label_preview = format_label(quotation, party_info)
    
    return jsonify({
        'status': 'success',
        'preview': label_preview
    })

@app.route('/print', methods=['POST'])
def print_label_route():
    """Handle print requests - printing happens on server side"""
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'})
        
    quotation = data.get('quotation')
    party = data.get('party')
    address = data.get('address', '')
    phone = data.get('phone', '')
    mobile = data.get('mobile', '')
    
    if not quotation or not party:
        return jsonify({'status': 'error', 'message': 'Quotation and party are required'})
    
    print(f"Server: Received print request for quotation {quotation}")
    
    # Call the print function (runs on server)
    success = print_label(quotation, party, address, phone, mobile)
    
    if success:
        print(f"Server: Successfully sent print job for quotation {quotation}")
        return jsonify({'status': 'printed', 'message': 'Label sent to printer successfully'})
    else:
        print(f"Server: Failed to print label for quotation {quotation}")
        return jsonify({'status': 'error', 'message': 'Failed to send label to printer'})

@app.route('/get-settings', methods=['GET'])
def get_settings():
    """Get current database and printer settings"""
    return jsonify({
        'server': DB_SERVER or '',
        'database': DB_NAME or '',
        'printer': SELECTED_PRINTER or ''
    })

@app.route('/get-printers', methods=['GET'])
def get_printers():
    """Get list of available printers"""
    printers = get_available_printers()
    return jsonify({'printers': printers})

@app.route('/save-settings', methods=['POST'])
def save_settings():
    """Save new database and printer settings"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    server = data.get('server', '').strip()
    database = data.get('database', '').strip()
    printer = data.get('printer', '').strip()
    
    if not server or not database:
        return jsonify({'success': False, 'error': 'Server and database name are required'})
    
    # Test the database connection before saving
    try:
        conn_str = (
            f"DRIVER={{SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"Trusted_Connection=yes;"
        )
        conn = pyodbc.connect(conn_str)
        conn.close()
        
        # Connection successful, save all settings
        if save_db_settings(server, database, printer if printer else None):
            if printer:
                print(f"Server: HARDCODED printer set to: {printer}")
                print(f"Server: All future print jobs will use: {printer}")
            else:
                print(f"Server: Printer selection cleared - will use default printer")
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save settings'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'Database connection failed: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)