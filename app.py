import os
import tempfile
import json
import logging
import sys
import threading
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, jsonify
import pyodbc
import subprocess
from dotenv import load_dotenv
load_dotenv()

import printed_db

app = Flask(__name__)

# Configure logging for service mode
def setup_logging():
    """Setup logging for both console and file output"""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure Flask app logging
    if not app.debug:
        # File logging with rotation
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, 'label_print_server.log'),
            maxBytes=1024 * 1024 * 10,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        
        # Console logging with proper encoding
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))
        
        # Add handlers to Flask logger
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
        
        # Log startup
        app.logger.info('Label Print Server starting up')

# Setup logging
setup_logging()

# Global variables for database settings
DB_SERVER = os.environ.get('DB_SERVER')
DB_NAME = os.environ.get('DB_NAME')
SETTINGS_FILE = 'db_settings.json'
SELECTED_PRINTER = None  # Will store the selected printer name
BARTENDER_TEMPLATE = None  # Will store the BarTender template path

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
    global DB_SERVER, DB_NAME, SELECTED_PRINTER, BARTENDER_TEMPLATE
    
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                DB_SERVER = settings.get('server', DB_SERVER)
                DB_NAME = settings.get('database', DB_NAME)
                SELECTED_PRINTER = settings.get('printer', None)
                BARTENDER_TEMPLATE = settings.get('bartender_template', None)
                print(f"Server: Loaded settings - Server: {DB_SERVER}, DB: {DB_NAME}, Printer: {SELECTED_PRINTER}")
                print(f"Server: BarTender Template: {BARTENDER_TEMPLATE}")
        except Exception as e:
            print(f"Error loading settings: {e}")

def save_db_settings(server, database, printer=None, bartender_template=None):
    """Save database, printer and BarTender settings to file"""
    global DB_SERVER, DB_NAME, SELECTED_PRINTER, BARTENDER_TEMPLATE
    
    try:
        settings = {
            'server': server, 
            'database': database,
            'printer': printer,
            'bartender_template': bartender_template
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
        
        # Update global variables
        DB_SERVER = server
        DB_NAME = database
        SELECTED_PRINTER = printer
        BARTENDER_TEMPLATE = bartender_template
        print(f"Server: Saved settings - Server: {server}, DB: {database}, Printer: {printer}")
        print(f"Server: BarTender Template: {bartender_template}")
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# Load settings on startup
load_db_settings()

# Initialize printed records DB
try:
    printed_db.init_db()
    print('Server: printed_records DB initialized')
except Exception as e:
    print(f'Server: Failed initializing printed DB: {e}')

# Log startup configuration
startup_msg = [
    "="*50,
    "LABEL PRINT SERVER STARTUP", 
    "="*50,
    f"Database Server: {DB_SERVER}",
    f"Database Name: {DB_NAME}"
]

if SELECTED_PRINTER:
    startup_msg.extend([
        f"HARDCODED Printer: {SELECTED_PRINTER}",
        "  -> All print jobs will go to this specific printer"
    ])
else:
    startup_msg.extend([
        "Printer: Default System Printer",
        "  -> Will use system default printer"
    ])

if BARTENDER_TEMPLATE:
    startup_msg.append(f"BarTender Template: {BARTENDER_TEMPLATE}")
else:
    startup_msg.append("BarTender: Not configured (using text printing)")

startup_msg.append("="*50)

# Print to console and log
for line in startup_msg:
    print(line)
    # Only log to file, avoid console encoding issues in service mode
    if hasattr(app, 'logger') and app.logger.handlers:
        # Log only to file handlers, not console
        for handler in app.logger.handlers:
            if isinstance(handler, RotatingFileHandler):
                handler.emit(app.logger.makeRecord(
                    app.logger.name, logging.INFO, __file__, 0, line, (), None
                ))

def get_party_info(quotation_number):
    # Format quotation number as 25-character string with 'G-' prefix, right-aligned
    formatted_vch_no = f"G-{quotation_number}".rjust(25)
    
    print(f"Searching for {formatted_vch_no}")
    
    # Check if database settings are configured
    if not DB_SERVER or not DB_NAME:
        print("Database error: Server or database not configured. Please check settings.")
        return None
    
    # Use the most compatible ODBC driver available
    available_drivers = pyodbc.drivers()
    driver = None
    
    # Prioritize drivers and use appropriate authentication
    if 'ODBC Driver 18 for SQL Server' in available_drivers:
        driver = 'ODBC Driver 18 for SQL Server'
        # ODBC Driver 18 requires specific authentication syntax
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=10;"
        )
    elif 'ODBC Driver 17 for SQL Server' in available_drivers:
        driver = 'ODBC Driver 17 for SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Integrated Security=SSPI;"
            f"Connection Timeout=10;"
        )
    elif 'SQL Server' in available_drivers:
        driver = 'SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout=10;"
        )
    else:
        print("Database error: No SQL Server ODBC drivers found")
        return None
    
    conn = None
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Step 1: Get MasterCode from Tran2 table
        cursor.execute("SELECT CM1 FROM dbo.Tran2 WHERE VchType='26' AND MasterCode2='201' AND VchNo=?", formatted_vch_no)
        tran_row = cursor.fetchone()
        
        if not tran_row or not tran_row.CM1:
            return None
            
        master_code = tran_row.CM1
        # print(f"Mastercode {master_code}")
        
        # Step 2: Get shop name from Master1 table
        cursor.execute("SELECT Name, Code FROM Master1 WHERE MasterType=2 AND Code=?", master_code)
        master_row = cursor.fetchone()
        
        if not master_row:
            return None
            
        shop_name = master_row.Name
        
        # Step 3: Get address information from MasterAddressInfo table
        cursor.execute("SELECT Address1, Address2, Address3, Address4, Telno, Mobile FROM MasterAddressInfo WHERE MasterCode=?", master_code)
        address_row = cursor.fetchone()
        
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
        
    except pyodbc.Error as e:
        error_code = e.args[0] if e.args else 'Unknown'
        error_msg = e.args[1] if len(e.args) > 1 else str(e)
        
        # Provide specific error messages based on error codes
        if error_code in ['08001', '08S01']:
            print(f"Database connection error: Cannot reach SQL Server '{DB_SERVER}'. Please check:")
            print("- Server name is correct")
            print("- SQL Server is running")
            print("- Network connectivity")
            print("- Firewall settings")
        elif error_code == '18456':
            print(f"Database authentication error: Access denied to '{DB_NAME}' database")
        elif error_code == 'IM002':
            print(f"Database driver error: ODBC driver not found or incompatible")
        else:
            print(f"Database error ({error_code}): {error_msg}")
            
        return None
        
    except Exception as e:
        print(f"Unexpected database error: {e}")
        return None
        
    finally:
        if conn:
            try:
                conn.close()
            except:
                pass

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

def print_label_bartender(quotation, party_info, bartender_template_path):
    """Print label using BarTender with template and data"""
    global SELECTED_PRINTER
    
    try:
        # Extract data for BarTender variables
        customer_name = party_info.get('name', '')
        address_parts = [
            party_info.get('address1', ''),
            party_info.get('address2', ''),
            party_info.get('address3', ''),
            party_info.get('address4', '')
        ]
        address = ', '.join([part.strip() for part in address_parts if part.strip()])
        phone = party_info.get('phone', '')
        mobile = party_info.get('mobile', '')
        
        # Combine phone and mobile into a single contact field
        contact_numbers = []
        if phone:
            contact_numbers.append(phone)
        if mobile:
            contact_numbers.append(mobile)
        combined_contact = ' | '.join(contact_numbers)  # Join with separator
        
        from datetime import datetime
        packed_time = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        # Log the print request
        print(f"Server: BarTender print request for quotation {quotation}")
        print(f"Server: Template: {bartender_template_path}")
        print(f"Server: Customer: {customer_name}")
        print(f"Server: Combined contact: {combined_contact}")
        
        # Method 1: Try BarTender Command Line Interface
        try:
            bartender_cmd = [
                'bartend.exe',
                bartender_template_path,
                '/AF=quotation_number=' + quotation,
                '/AF=customer_name=' + customer_name,
                '/AF=address=' + address,
                '/AF=mobile=' + combined_contact,
                '/AF=packed_time=' + packed_time,
                '/P'  # Print command
            ]
            
            # Add printer selection if specified
            if SELECTED_PRINTER:
                bartender_cmd.append(f'/PRN={SELECTED_PRINTER}')
                print(f"Server: Using HARDCODED BarTender printer: {SELECTED_PRINTER}")
            else:
                print(f"Server: Using default BarTender printer")
            
            # Close BarTender after printing
            bartender_cmd.append('/C')
            
            result = subprocess.run(bartender_cmd,
                                  capture_output=True,
                                  text=True,
                                  timeout=30,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                print(f"Server: BarTender print successful")
                return True
            else:
                print(f"Server: BarTender CLI failed: {result.stderr}")
                
        except Exception as cli_error:
            print(f"Server: BarTender CLI method failed: {cli_error}")
        
        # Method 2: Try BarTender COM Interface (if CLI fails)
        try:
            import win32com.client
            
            print("Server: Trying BarTender COM interface")
            
            # Create BarTender application object
            bt_app = win32com.client.Dispatch("BarTender.Application")
            
            # bt_app.Visible = True # Make BarTender visible for debugging
            
            bt_format = bt_app.Formats.Open(bartender_template_path, False, "")
            
            # Set data sources/variables
            bt_format.SetNamedSubStringValue("quotation_number", quotation)
            bt_format.SetNamedSubStringValue("customer_name", customer_name)
            bt_format.SetNamedSubStringValue("address", address)
            bt_format.SetNamedSubStringValue("mobile", combined_contact)
            bt_format.SetNamedSubStringValue("packed_time", packed_time)
            
            # Print the label
            if SELECTED_PRINTER:
                # Set the printer for this format
                bt_format.Printer = SELECTED_PRINTER
                print(f"Server: BarTender printer set to: {SELECTED_PRINTER}")
                
                # Use PrintOut with correct parameters (PrintDialog, JobDialog)
                bt_format.PrintOut(False, False)  # False, False = no print dialog, no job dialog
            else:
                bt_format.PrintOut(False, False)
            
            # Close the format and application
            bt_format.Close(0)  # 0 = don't save changes
            bt_app.Quit(0)      # 0 = don't save changes
            
            print(f"Server: BarTender COM print successful")
            return True
                
        except Exception as com_error:
            print(f"Server: BarTender COM method failed: {com_error}")
        return False
    except Exception as e:
        print(f"Server: BarTender print error: {e}")
        return False

def print_label(quotation, party, address='', phone='', mobile=''):
    """Print label using BarTender (if template configured) or fallback to text printing"""
    global SELECTED_PRINTER, BARTENDER_TEMPLATE
    
    try:
        # Create party info dictionary for BarTender
        party_info = {
            'name': party,
            'address1': address.split(',')[0].strip() if address else '',
            'address2': ','.join(address.split(',')[1:]).strip() if ',' in address else '',
            'address3': '',
            'address4': '',
            'phone': phone,
            'mobile': mobile
        }
        
        # Try BarTender printing first if template is configured
        if BARTENDER_TEMPLATE and os.path.exists(BARTENDER_TEMPLATE):
            print(f"Server: Using BarTender template: {BARTENDER_TEMPLATE}")
            success = print_label_bartender(quotation, party_info, BARTENDER_TEMPLATE)
            if success:
                return True
            else:
                print(f"Server: BarTender failed, falling back to text printing")
        else:
            if BARTENDER_TEMPLATE:
                print(f"Server: BarTender template not found: {BARTENDER_TEMPLATE}")
            else:
                print(f"Server: No BarTender template configured, using text printing")
        
        # Fallback to text-based printing (original method)
        return print_label_text(quotation, party_info)
        
    except Exception as e:
        print(f"Server: Print error: {e}")
        return False

def print_label_text(quotation, party_info):
    """Original text-based printing method (fallback)"""
    global SELECTED_PRINTER
    
    try:
        # Use the professional label formatting
        label_text = format_label(quotation, party_info)
        
        # Log which printer will be used
        printer_to_use = SELECTED_PRINTER if SELECTED_PRINTER else "Default System Printer"
        print(f"Server: Text printing for quotation {quotation}")
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
        print("Server: Text print command timed out")
        return False
    except Exception as e:
        print(f"Server: Text print error: {e}")
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
        try:
            printed_db.record_print(quotation, party=party, address=address, phone=phone, mobile=mobile)
            print(f"Server: Recorded printed quotation {quotation} in local DB")
        except Exception as e:
            print(f"Server: Failed to record printed quotation: {e}")
        return jsonify({'status': 'printed', 'message': 'Label sent to printer successfully'})
    else:
        print(f"Server: Failed to print label for quotation {quotation}")
        return jsonify({'status': 'error', 'message': 'Failed to send label to printer'})

@app.route('/get-settings', methods=['GET'])
def get_settings():
    """Get current database, printer and BarTender settings"""
    return jsonify({
        'server': DB_SERVER or '',
        'database': DB_NAME or '',
        'printer': SELECTED_PRINTER or '',
        'bartender_template': BARTENDER_TEMPLATE or ''
    })

@app.route('/get-printers', methods=['GET'])
def get_printers():
    """Get list of available printers"""
    printers = get_available_printers()
    return jsonify({'printers': printers})


@app.route('/printed-records', methods=['GET'])
def printed_records():
    try:
        # Pagination params
        try:
            page = int(request.args.get('page', '1'))
            page_size = int(request.args.get('page_size', '50'))
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 50
        except Exception:
            page = 1
            page_size = 50

        q = request.args.get('q')
        offset = (page - 1) * page_size
        data = printed_db.get_recent(limit=page_size, q=q, offset=offset)
        total = data.get('total', 0)
        records = data.get('records', [])
        has_more = (offset + len(records)) < total
        return jsonify({'success': True, 'records': records, 'total': total, 'page': page, 'page_size': page_size, 'has_more': has_more})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/save-settings', methods=['POST'])
def save_settings():
    """Save new database, printer and BarTender settings"""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    server = data.get('server', '').strip()
    database = data.get('database', '').strip()
    printer = data.get('printer', '').strip()
    bartender_template = data.get('bartender_template', '').strip()
    
    if not server or not database:
        return jsonify({'success': False, 'error': 'Server and database name are required'})
    
    # Test the database connection before saving
    try:
        # Use the same driver selection logic as the main app
        available_drivers = pyodbc.drivers()
        
        if 'ODBC Driver 18 for SQL Server' in available_drivers:
            conn_str = (
                f"DRIVER={{ODBC Driver 18 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=10;"
            )
        elif 'ODBC Driver 17 for SQL Server' in available_drivers:
            conn_str = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Integrated Security=SSPI;"
                f"Connection Timeout=10;"
            )
        else:
            conn_str = (
                f"DRIVER={{SQL Server}};"
                f"SERVER={server};"
                f"DATABASE={database};"
                f"Trusted_Connection=yes;"
                f"Connection Timeout=10;"
            )
            
        conn = pyodbc.connect(conn_str)
        conn.close()
        
        # Connection successful, save all settings
        if save_db_settings(server, database, printer if printer else None, bartender_template if bartender_template else None):
            if printer:
                print(f"Server: HARDCODED printer set to: {printer}")
                print(f"Server: All future print jobs will use: {printer}")
            else:
                print(f"Server: Printer selection cleared - will use default printer")
                
            if bartender_template:
                if os.path.exists(bartender_template):
                    print(f"Server: BarTender template configured: {bartender_template}")
                else:
                    print(f"Server: WARNING - BarTender template file not found: {bartender_template}")
            else:
                print(f"Server: BarTender template cleared - will use text printing")
                
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save settings'})
            
    except Exception as e:
            return jsonify({'success': False, 'error': f'Database connection failed: {str(e)}'})

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """Test database connection with current or provided settings"""
    data = request.json or {}
    
    # Use provided settings or current ones
    test_server = data.get('server', DB_SERVER)
    test_database = data.get('database', DB_NAME)
    
    if not test_server or not test_database:
        return jsonify({
            'success': False, 
            'error': 'Server and database name are required',
            'details': 'Please configure database settings first'
        })
    
    # Get available drivers
    available_drivers = pyodbc.drivers()
    sql_drivers = [d for d in available_drivers if 'SQL Server' in d]
    
    if not sql_drivers:
        return jsonify({
            'success': False,
            'error': 'No SQL Server ODBC drivers found',
            'details': 'Please install SQL Server ODBC drivers'
        })
    
    # Try multiple drivers in order of preference with correct authentication
    results = []
    
    # Test ODBC Driver 18 for SQL Server (with proper authentication)
    if 'ODBC Driver 18 for SQL Server' in available_drivers:
        driver = 'ODBC Driver 18 for SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={test_server};"
            f"DATABASE={test_database};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout=10;"
        )
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1")
            basic_test = cursor.fetchone()[0] == 1
            
            # Test required tables
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('Tran2', 'Master1', 'MasterAddressInfo')
            """)
            table_count = cursor.fetchone()[0]
            
            # Get SQL Server version
            cursor.execute("SELECT @@VERSION")
            version_info = cursor.fetchone()[0].split('\n')[0]
            
            conn.close()
            
            return jsonify({
                'success': True,
                'driver': driver,
                'version': version_info,
                'tables_found': f"{table_count}/3 required tables",
                'message': f'Successfully connected using {driver}',
                'connection_string': conn_str.replace(test_server, '[SERVER]').replace(test_database, '[DATABASE]')
            })
            
        except Exception as e:
            results.append({
                'driver': driver,
                'success': False,
                'error': str(e)
            })
    
    # Test ODBC Driver 17 for SQL Server
    if 'ODBC Driver 17 for SQL Server' in available_drivers:
        driver = 'ODBC Driver 17 for SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={test_server};"
            f"DATABASE={test_database};"
            f"Integrated Security=SSPI;"
            f"Connection Timeout=10;"
        )
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1")
            basic_test = cursor.fetchone()[0] == 1
            
            # Test required tables
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('Tran2', 'Master1', 'MasterAddressInfo')
            """)
            table_count = cursor.fetchone()[0]
            
            # Get SQL Server version
            cursor.execute("SELECT @@VERSION")
            version_info = cursor.fetchone()[0].split('\n')[0]
            
            conn.close()
            
            return jsonify({
                'success': True,
                'driver': driver,
                'version': version_info,
                'tables_found': f"{table_count}/3 required tables",
                'message': f'Successfully connected using {driver}',
                'connection_string': conn_str.replace(test_server, '[SERVER]').replace(test_database, '[DATABASE]')
            })
            
        except Exception as e:
            results.append({
                'driver': driver,
                'success': False,
                'error': str(e)
            })
    
    # Test legacy SQL Server driver
    if 'SQL Server' in available_drivers:
        driver = 'SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={test_server};"
            f"DATABASE={test_database};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout=10;"
        )
        
        try:
            conn = pyodbc.connect(conn_str)
            cursor = conn.cursor()
            
            # Test basic connectivity
            cursor.execute("SELECT 1")
            basic_test = cursor.fetchone()[0] == 1
            
            # Test required tables
            cursor.execute("""
                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME IN ('Tran2', 'Master1', 'MasterAddressInfo')
            """)
            table_count = cursor.fetchone()[0]
            
            # Get SQL Server version
            cursor.execute("SELECT @@VERSION")
            version_info = cursor.fetchone()[0].split('\n')[0]
            
            conn.close()
            
            return jsonify({
                'success': True,
                'driver': driver,
                'version': version_info,
                'tables_found': f"{table_count}/3 required tables",
                'message': f'Successfully connected using {driver}',
                'connection_string': conn_str.replace(test_server, '[SERVER]').replace(test_database, '[DATABASE]')
            })
            
        except Exception as e:
            error_details = str(e)
            results.append({
                'driver': driver,
                'success': False,
                'error': error_details
            })
    
    # If all drivers failed, return detailed error information
    return jsonify({
        'success': False,
        'error': f'Unable to connect to SQL Server {test_server}',
        'available_drivers': sql_drivers,
        'test_results': results,
        'suggestions': [
            'Check if SQL Server is running',
            'Verify server name is correct',
            'Ensure SQL Server allows remote connections',
            'Check Windows Firewall settings',
            'Try using IP address instead of server name',
            'Verify your Windows user has database access'
        ]
    })

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """Shutdown the server"""
    # Try the Werkzeug shutdown first (works when running via flask run)
    func = request.environ.get('werkzeug.server.shutdown')
    if func:
        func()
        return 'Server shutting down...'

    # When not running under Werkzeug (e.g., waitress), accept token-authenticated
    # shutdown requests similar to /control for backwards compatibility.
    try:
        data = request.get_json(force=True)
    except Exception:
        data = {}

    token = data.get('token')
    token_file = os.path.join(os.path.dirname(__file__), '.tray_control_token')
    expected = None
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                expected = f.read().strip()
        except Exception:
            expected = None

    if token and expected and token == expected:
        # schedule delayed exit (so client gets response)
        def delayed_exit():
            import time
            time.sleep(0.25)
            os._exit(0)

        t = threading.Thread(target=delayed_exit, daemon=True)
        t.start()
        try:
            os.remove(token_file)
        except Exception:
            pass
        return 'Server shutting down (via control token)'

    # If we get here, Werkzeug wasn't available and token auth failed
    return jsonify({'success': False, 'error': 'Not running with the Werkzeug Server; use /control or provide token'}), 500


# Global flag for tray-managed shutdown
_stop_requested = False

@app.route('/control', methods=['POST'])
def control():
    """Internal control endpoint for tray GUI. Expects JSON {action: 'stop', token: '...'}"""
    global _stop_requested
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({'success': False, 'error': 'Invalid JSON'}), 400

    action = data.get('action')
    token = data.get('token')

    # check token file
    token_file = os.path.join(os.path.dirname(__file__), '.tray_control_token')
    expected = None
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r') as f:
                expected = f.read().strip()
        except Exception:
            expected = None

    if token != expected:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    if action == 'stop':
        # Set flag that tray_app can check to trigger server shutdown
        _stop_requested = True
        print('Control: stop action received, flag set for tray')
        
        # Create stop signal file for tray_app
        stop_signal_file = os.path.join(os.path.dirname(__file__), '.tray_stop_signal')
        try:
            with open(stop_signal_file, 'w') as f:
                f.write('stop')
            print('Created stop signal file')
        except Exception as e:
            print(f'Error creating stop signal: {e}')
        
        try:
            os.remove(token_file)
        except Exception:
            pass
        return jsonify({'success': True, 'message': 'Server stop requested'})
    
    elif action == 'quit':
        # Set flag and also create quit signal for tray app to exit completely
        _stop_requested = True
        print('Control: quit action received, signaling complete shutdown')
        
        # Create quit signal file for tray_app
        quit_signal_file = os.path.join(os.path.dirname(__file__), '.tray_quit_signal')
        try:
            with open(quit_signal_file, 'w') as f:
                f.write('quit')
        except Exception as e:
            print(f'Error creating quit signal: {e}')
        
        try:
            os.remove(token_file)
        except Exception:
            pass
        return jsonify({'success': True, 'message': 'Complete shutdown requested'})
    
    elif action == 'start':
        # Create start signal file for tray_app
        print('Control: start action received, signaling server start')
        start_signal_file = os.path.join(os.path.dirname(__file__), '.tray_start_signal')
        try:
            with open(start_signal_file, 'w') as f:
                f.write('start')
            print('Created start signal file')
        except Exception as e:
            print(f'Error creating start signal: {e}')
        
        return jsonify({'success': True, 'message': 'Server start requested'})

    return jsonify({'success': False, 'error': 'Unknown action'}), 400

if __name__ == '__main__':
    # This will run when called directly (not as a service)
    print("Starting Label Print Server in development mode...")
    print("For production deployment, use the Windows service:")
    print("  python service.py install")
    print("  python service.py start")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)