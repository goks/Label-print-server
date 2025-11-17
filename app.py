import os
import tempfile
import json
import logging
import sys
import threading
import traceback
import time
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from flask import Flask, render_template, request, jsonify, g
from werkzeug.middleware.proxy_fix import ProxyFix
import pyodbc
import subprocess
from dotenv import load_dotenv
from functools import lru_cache
from queue import Queue, Empty
load_dotenv()

import printed_db
from update_manager import UpdateManager, UpdateChecker

# Production configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max request size
    DATABASE_CONNECTION_TIMEOUT = 30
    REQUEST_TIMEOUT = 60
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'production')
    # Connection pool settings
    DB_POOL_SIZE = int(os.environ.get('DB_POOL_SIZE', '5'))
    DB_POOL_TIMEOUT = int(os.environ.get('DB_POOL_TIMEOUT', '30'))

# Database Connection Pool
class DatabaseConnectionPool:
    """Thread-safe connection pool for SQL Server"""
    def __init__(self, pool_size=5):
        self.pool_size = pool_size
        self.pool = Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self.active_connections = 0
        self.conn_string = None
        
    def initialize(self, conn_string):
        """Initialize the connection pool with a connection string"""
        self.conn_string = conn_string
        # Pre-create connections
        for _ in range(self.pool_size):
            try:
                conn = pyodbc.connect(conn_string)
                self.pool.put(conn)
                self.active_connections += 1
            except Exception as e:
                print(f"Failed to create pooled connection: {e}")
                break
    
    def get_connection(self, timeout=30):
        """Get a connection from the pool"""
        try:
            conn = self.pool.get(timeout=timeout)
            # Test if connection is still valid
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return conn
            except:
                # Connection is stale, create a new one
                try:
                    conn.close()
                except:
                    pass
                if self.conn_string:
                    conn = pyodbc.connect(self.conn_string)
                    return conn
                else:
                    raise Exception("Connection pool not initialized")
        except Empty:
            # Pool is empty, create a temporary connection
            if self.conn_string:
                return pyodbc.connect(self.conn_string)
            else:
                raise Exception("Connection pool not initialized and no connection string available")
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        try:
            # Try to return to pool, but don't block if full
            self.pool.put_nowait(conn)
        except:
            # Pool is full, close the connection
            try:
                conn.close()
            except:
                pass
    
    def close_all(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except:
                pass

# Global connection pool
db_pool = DatabaseConnectionPool(pool_size=Config.DB_POOL_SIZE)

app = Flask(__name__)
app.config.from_object(Config)

# Configure for reverse proxy deployment
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

def setup_comprehensive_logging():
    """Setup comprehensive production logging with multiple handlers"""
    # Use AppData/Local for logs when installed in Program Files
    app_dir = os.path.dirname(__file__)
    if 'Program Files' in app_dir:
        # Running from installation - use user's AppData
        log_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 
                               'LabelPrintServer', 'logs')
    else:
        # Running from development directory
        log_dir = os.path.join(app_dir, 'logs')
    
    os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 1. Main application log (daily rotation)
    app_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'label_print_server.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(detailed_formatter)
    
    # 2. Error log (separate file for errors only)
    error_handler = RotatingFileHandler(
        os.path.join(log_dir, 'errors.log'),
        maxBytes=50 * 1024 * 1024,  # 50MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    
    # 3. Database operations log
    db_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'database.log'),
        when='midnight',
        interval=1,
        backupCount=14,
        encoding='utf-8'
    )
    db_handler.setLevel(logging.DEBUG)
    db_handler.setFormatter(detailed_formatter)
    
    # 4. Security/Access log
    access_handler = TimedRotatingFileHandler(
        os.path.join(log_dir, 'access.log'),
        when='midnight',
        interval=1,
        backupCount=90,
        encoding='utf-8'
    )
    access_handler.setLevel(logging.INFO)
    access_handler.setFormatter(logging.Formatter(
        '%(asctime)s | %(message)s'
    ))
    
    # 5. Console handler for production monitoring
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)  # Only warnings and above to console
    console_handler.setFormatter(simple_formatter)
    
    # Add handlers to loggers
    app.logger.addHandler(app_handler)
    app.logger.addHandler(error_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(logging.INFO)
    
    # Create specialized loggers
    db_logger = logging.getLogger('database')
    db_logger.addHandler(db_handler)
    db_logger.setLevel(logging.DEBUG)
    
    access_logger = logging.getLogger('access')
    access_logger.addHandler(access_handler)
    access_logger.setLevel(logging.INFO)
    
    # Suppress noisy third-party loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    return db_logger, access_logger

# Setup logging
db_logger, access_logger = setup_comprehensive_logging()
app.logger.info('Label Print Server starting up in %s mode', Config.ENVIRONMENT)

# Production middleware and error handling
@app.before_request
def before_request():
    """Log request and set up request context"""
    g.start_time = time.time()
    g.request_id = os.urandom(8).hex()
    
    # Only log non-health-check requests in production to reduce noise
    if Config.LOG_LEVEL == 'DEBUG' or (request.endpoint and request.endpoint not in ['static', 'health_check', 'metrics']):
        if not request.endpoint or not request.endpoint.startswith('static'):
            access_logger.info(
                'Request %s: %s %s from %s',
                g.request_id,
                request.method,
                request.path,  # Use path instead of url to reduce log size
                request.remote_addr
            )

@app.after_request
def after_request(response):
    """Log response and performance metrics"""
    if hasattr(g, 'start_time'):
        duration = round((time.time() - g.start_time) * 1000, 2)  # milliseconds
        
        # Only log important responses or slow requests
        is_important = request.endpoint not in ['static', 'health_check', 'metrics'] if request.endpoint else True
        is_slow = duration > 1000  # 1 second
        is_error = response.status_code >= 400
        
        if Config.LOG_LEVEL == 'DEBUG' or is_slow or is_error:
            if is_important:
                access_logger.info(
                    'Response %s: %s %s - Status: %d - Duration: %sms',
                    g.request_id,
                    request.method,
                    request.path,
                    response.status_code,
                    duration
                )
        
        # Log slow requests as warnings
        if duration > 5000:  # 5 seconds
            app.logger.warning(
                'SLOW REQUEST: %s %s took %sms',
                request.method,
                request.path,
                duration
            )
    
    # Security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    return response

@app.errorhandler(404)
def not_found_error(error):
    app.logger.warning('404 error: %s requested %s', request.remote_addr, request.url)
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error('500 error on %s: %s', request.url, str(error), exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(Exception)
def unhandled_exception(error):
    app.logger.error('Unhandled exception: %s', str(error), exc_info=True)
    return jsonify({'error': 'An unexpected error occurred'}), 500

# Global variables for database settings
DB_SERVER = os.environ.get('DB_SERVER')
DB_NAME = os.environ.get('DB_NAME')

# Use AppData for settings when installed in Program Files
app_dir = os.path.dirname(__file__)
if 'Program Files' in app_dir:
    # Running from installation - use user's AppData
    data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 
                           'LabelPrintServer', 'data')
    os.makedirs(data_dir, exist_ok=True)
    SETTINGS_FILE = os.path.join(data_dir, 'db_settings.json')
else:
    # Running from development directory
    SETTINGS_FILE = 'db_settings.json'

SELECTED_PRINTER = None  # Will store the selected printer name
BARTENDER_TEMPLATE = None  # Will store the BarTender template path

# Settings cache with lock for thread-safety
_settings_cache = {
    'server': None,
    'database': None,
    'printer': None,
    'bartender_template': None,
    'last_loaded': None
}
_settings_lock = threading.Lock()

# Printer list cache
_printer_cache = {
    'printers': None,
    'last_updated': None,
    'ttl': 60  # Cache printers for 60 seconds
}
_printer_cache_lock = threading.Lock()

# Update system globals
update_manager = None
update_checker = None

def get_available_printers():
    """Get list of available printers on Windows with caching"""
    global _printer_cache
    
    # Check cache first
    with _printer_cache_lock:
        if _printer_cache['printers'] is not None and _printer_cache['last_updated'] is not None:
            cache_age = time.time() - _printer_cache['last_updated']
            if cache_age < _printer_cache['ttl']:
                return _printer_cache['printers']
    
    # Cache miss or expired, fetch printers
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
            
            # Update cache
            with _printer_cache_lock:
                _printer_cache['printers'] = printers
                _printer_cache['last_updated'] = time.time()
            
            return printers
        else:
            print(f"Server: Failed to get printers: {result.stderr}")
            return []
            
    except Exception as e:
        print(f"Server: Error getting printers: {e}")
        return []

def load_db_settings():
    """Load database settings from file or environment variables with caching"""
    global DB_SERVER, DB_NAME, SELECTED_PRINTER, BARTENDER_TEMPLATE, _settings_cache
    
    # Check if settings are already cached in memory
    with _settings_lock:
        if _settings_cache['last_loaded'] is not None:
            # Return cached values
            DB_SERVER = _settings_cache['server']
            DB_NAME = _settings_cache['database']
            SELECTED_PRINTER = _settings_cache['printer']
            BARTENDER_TEMPLATE = _settings_cache['bartender_template']
            return
    
    # Load from file if not cached
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
                DB_SERVER = settings.get('server', DB_SERVER)
                DB_NAME = settings.get('database', DB_NAME)
                SELECTED_PRINTER = settings.get('printer', None)
                BARTENDER_TEMPLATE = settings.get('bartender_template', None)
                
                # Update cache
                with _settings_lock:
                    _settings_cache['server'] = DB_SERVER
                    _settings_cache['database'] = DB_NAME
                    _settings_cache['printer'] = SELECTED_PRINTER
                    _settings_cache['bartender_template'] = BARTENDER_TEMPLATE
                    _settings_cache['last_loaded'] = time.time()
                
                print(f"Server: Loaded settings - Server: {DB_SERVER}, DB: {DB_NAME}, Printer: {SELECTED_PRINTER}")
                print(f"Server: BarTender Template: {BARTENDER_TEMPLATE}")
        except Exception as e:
            print(f"Error loading settings: {e}")

def save_db_settings(server, database, printer=None, bartender_template=None):
    """Save database, printer and BarTender settings to file and update cache"""
    global DB_SERVER, DB_NAME, SELECTED_PRINTER, BARTENDER_TEMPLATE, _settings_cache
    
    try:
        settings = {
            'server': server, 
            'database': database,
            'printer': printer,
            'bartender_template': bartender_template
        }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
        
        # Update global variables and cache atomically
        with _settings_lock:
            DB_SERVER = server
            DB_NAME = database
            SELECTED_PRINTER = printer
            BARTENDER_TEMPLATE = bartender_template
            _settings_cache['server'] = server
            _settings_cache['database'] = database
            _settings_cache['printer'] = printer
            _settings_cache['bartender_template'] = bartender_template
            _settings_cache['last_loaded'] = time.time()
        
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

# LRU cache for quotation lookups (cache up to 100 recent lookups for 5 minutes)
@lru_cache(maxsize=100)
def _get_party_info_cached(quotation_number, cache_key):
    """Internal cached function for party info lookup - cache_key forces cache refresh"""
    return _get_party_info_impl(quotation_number)

def _get_party_info_impl(quotation_number):
    """Implementation of party info lookup with connection pooling"""
    start_time = time.time()
    
    # Format quotation number as 25-character string with 'G-' prefix, right-aligned
    formatted_vch_no = f"G-{quotation_number}".rjust(25)
    
    if Config.LOG_LEVEL == 'DEBUG':
        db_logger.debug('Database lookup started: quotation=%s, formatted=%s', quotation_number, formatted_vch_no)
    
    # Check if database settings are configured
    if not DB_SERVER or not DB_NAME:
        db_logger.error('Database configuration missing: server=%s, database=%s', DB_SERVER, DB_NAME)
        return None
    
    # Use the most compatible ODBC driver available
    available_drivers = pyodbc.drivers()
    driver = None
    
    # Prioritize drivers and use appropriate authentication
    if 'ODBC Driver 18 for SQL Server' in available_drivers:
        driver = 'ODBC Driver 18 for SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"TrustServerCertificate=yes;"
            f"Connection Timeout={Config.DATABASE_CONNECTION_TIMEOUT};"
        )
    elif 'ODBC Driver 17 for SQL Server' in available_drivers:
        driver = 'ODBC Driver 17 for SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Integrated Security=SSPI;"
            f"Connection Timeout={Config.DATABASE_CONNECTION_TIMEOUT};"
        )
    elif 'SQL Server' in available_drivers:
        driver = 'SQL Server'
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={DB_SERVER};"
            f"DATABASE={DB_NAME};"
            f"Trusted_Connection=yes;"
            f"Connection Timeout={Config.DATABASE_CONNECTION_TIMEOUT};"
        )
    else:
        db_logger.error('No SQL Server ODBC drivers found. Available drivers: %s', available_drivers)
        return None
    
    # Initialize connection pool if needed
    if db_pool.conn_string != conn_str:
        db_pool.close_all()
        db_pool.initialize(conn_str)
    
    conn = None
    use_pool = True
    
    try:
        connection_start = time.time()
        
        # Try to get connection from pool
        try:
            conn = db_pool.get_connection(timeout=5)
            connection_time = time.time() - connection_start
            if Config.LOG_LEVEL == 'DEBUG':
                db_logger.debug('Got pooled connection in %.3f seconds', connection_time)
        except:
            # Fallback to direct connection if pool fails
            conn = pyodbc.connect(conn_str)
            use_pool = False
            connection_time = time.time() - connection_start
            db_logger.warning('Used direct connection (pool unavailable) in %.3f seconds', connection_time)
        
        cursor = conn.cursor()
        
        # Optimized: Use a single JOIN query instead of 3 sequential queries
        query_start = time.time()
        optimized_query = """
            SELECT 
                m.Name, m.Code,
                a.Address1, a.Address2, a.Address3, a.Address4,
                a.Telno, a.Mobile
            FROM dbo.Tran2 t
            INNER JOIN Master1 m ON t.CM1 = m.Code AND m.MasterType = 2
            LEFT JOIN MasterAddressInfo a ON m.Code = a.MasterCode
            WHERE t.VchType = '26' AND t.MasterCode2 = '201' AND t.VchNo = ?
        """
        
        if Config.LOG_LEVEL == 'DEBUG':
            db_logger.debug('Executing optimized query with parameter: %s', formatted_vch_no)
        
        cursor.execute(optimized_query, formatted_vch_no)
        row = cursor.fetchone()
        query_time = time.time() - query_start
        
        if not row:
            if Config.LOG_LEVEL == 'DEBUG':
                db_logger.info('No quotation found for %s (query completed in %.3fs)', quotation_number, query_time)
            return None
        
        # Compile party information from single query result
        party_info = {
            'name': row.Name if row.Name else '',
            'code': row.Code if row.Code else '',
            'address1': row.Address1 if row.Address1 else '',
            'address2': row.Address2 if row.Address2 else '',
            'address3': row.Address3 if row.Address3 else '',
            'address4': row.Address4 if row.Address4 else '',
            'phone': row.Telno if row.Telno else '',
            'mobile': row.Mobile if row.Mobile else ''
        }
        
        total_time = time.time() - start_time
        db_logger.info('Retrieved customer info for quotation %s in %.3fs: %s', 
                      quotation_number, total_time, party_info['name'])
        
        return party_info
        
    except pyodbc.Error as e:
        error_code = e.args[0] if e.args else 'Unknown'
        error_msg = e.args[1] if len(e.args) > 1 else str(e)
        elapsed_time = time.time() - start_time
        
        # Log detailed error information
        db_logger.error(
            'Database error for quotation %s (%.3fs): Code=%s, Message=%s',
            quotation_number, elapsed_time, error_code, error_msg
        )
        
        # Provide specific error messages based on error codes
        if error_code in ['08001', '08S01']:
            db_logger.error('Network connectivity issue to SQL Server %s', DB_SERVER)
        elif error_code == '18456':
            db_logger.error('Authentication failed for database %s', DB_NAME)
        elif error_code == '28000':
            db_logger.error('Login failed - likely authentication method issue')
        elif error_code == 'IM002':
            db_logger.error('ODBC driver compatibility issue')
        else:
            db_logger.error('Unhandled database error: %s', error_msg)
        
        return None
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        db_logger.error(
            'Unexpected database error for quotation %s (%.3fs): %s',
            quotation_number, elapsed_time, str(e), exc_info=True
        )
        return None
        
    finally:
        if conn:
            try:
                if use_pool:
                    # Return connection to pool
                    db_pool.return_connection(conn)
                else:
                    # Close direct connection
                    conn.close()
            except Exception as close_error:
                db_logger.warning('Error handling connection cleanup: %s', close_error)

def get_party_info(quotation_number):
    """Look up customer information from database with caching and connection pooling"""
    # Use cache with 5-minute TTL (cache_key changes every 5 minutes)
    cache_key = int(time.time() / 300)  # 300 seconds = 5 minutes
    return _get_party_info_cached(quotation_number, cache_key)

def format_label(quotation, party_info, copy_number=None, total_copies=None):
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
    
    # Line 1: Quotation number with optional copy info
    if copy_number is not None and total_copies is not None and total_copies > 1:
        label_lines.append(f"Q: {quotation} ({copy_number} of {total_copies})")
    else:
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

def print_label_bartender(quotation, party_info, bartender_template_path, copies=1):
    """Print label using BarTender with template and data - simple copy count"""
    global SELECTED_PRINTER
    
    # Validate copies
    if copies < 1:
        copies = 1
    
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
        
        # Format quotation - keep original quotation number
        quotation_display = quotation
        
        # Log the print request
        if copies > 1:
            print(f"Server: BarTender print request for quotation {quotation_display} - {copies} copies")
        else:
            print(f"Server: BarTender print request for quotation {quotation_display}")
        print(f"Server: Template: {bartender_template_path}")
        print(f"Server: Customer: {customer_name}")
        print(f"Server: Combined contact: {combined_contact}")
        
        # # Method 1: Try BarTender COM Interface (Primary)
        try:
            import win32com.client
            import pythoncom
            
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            
            print(f"Server: Using BarTender COM interface - {copies} copies")
            
            # Create BarTender application object
            bt_app = win32com.client.Dispatch("BarTender.Application")
            
            # bt_app.Visible = True # Make BarTender visible for debugging
            
            bt_format = bt_app.Formats.Open(bartender_template_path, False, "")
            
            # Set data sources/variables
            bt_format.SetNamedSubStringValue("quotation_number", quotation_display)
            bt_format.SetNamedSubStringValue("customer_name", customer_name)
            bt_format.SetNamedSubStringValue("address", address)
            bt_format.SetNamedSubStringValue("mobile", combined_contact)
            bt_format.SetNamedSubStringValue("packed_time", packed_time)
            bt_format.SetNamedSubStringValue("no_of_copies", 1)
            bt_format.SetNamedSubStringValue("no_of_serialized_labels", copies)
            
            # Print with specified number of copies
            if SELECTED_PRINTER:
                # Set the printer for this format
                bt_format.Printer = SELECTED_PRINTER
                print(f"Server: BarTender printer set to: {SELECTED_PRINTER}")
                
                # Set number of serialized labels (user input for copies)
                # bt_format.PrintSetup.NumberOfSerializedLabels = copies
                # bt_format.PrintSetup.IdenticalCopiesOfLabel = 1
                bt_format.PrintOut(False, False)
            else:
                # bt_format.PrintSetup.NumberOfSerializedLabels = copies
                # bt_format.PrintSetup.IdenticalCopiesOfLabel = 1
                bt_format.PrintOut(False, False)
            
            # Close the format and application
            bt_format.Close(0)  # 0 = don't save changes
            bt_app.Quit(0)      # 0 = don't save changes
            
            # Uninitialize COM
            pythoncom.CoUninitialize()
            
            if copies > 1:
                print(f"Server: BarTender COM print successful - {copies} copies")
            else:
                print(f"Server: BarTender COM print successful")
            return True
                
        except Exception as com_error:
            # Make sure to uninitialize COM even on error
            try:
                pythoncom.CoUninitialize()
            except:
                pass
            print(f"Server: BarTender COM method failed: {com_error}")
            app.logger.warning(f"BarTender COM failed, trying CLI fallback: {com_error}")
        
        # Method 2: BarTender Command Line Interface (Fallback)
        try:
            bartender_cmd = [
                'bartend.exe',
                bartender_template_path,
                '/AF=quotation_number=' + quotation_display,
                '/AF=customer_name=' + customer_name,
                '/AF=address=' + address,
                '/AF=mobile=' + combined_contact,
                '/AF=packed_time=' + packed_time,
                # '/AF=copy_number=1/' + str(copies),
                f'/S={copies}',  # Number of copies
                '/C=1',  # Number of copies
                '/P',  # Print command
                '/X'   # Exit after printing
            ]
            
            # Add printer selection if specified
            if SELECTED_PRINTER:
                bartender_cmd.append(f'/PRN={SELECTED_PRINTER}')
                app.logger.info(f"Fast BarTender print to: {SELECTED_PRINTER}")
                print("bartender_cmd:", bartender_cmd)
            else:
                print(f"Server: Using default BarTender printer")
            
            # Use Popen for non-blocking BarTender execution
            process = subprocess.Popen(bartender_cmd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Set a short timeout for immediate response
            try:
                stdout, stderr = process.communicate(timeout=3)  # 3 second max wait
                if process.returncode == 0:
                    app.logger.info(f"BarTender CLI print dispatched - {copies} copies")
                    return True
                else:
                    app.logger.warning(f"BarTender dispatch warning: {stderr.decode() if stderr else 'Unknown'}")
                    return True  # Still consider success since job was dispatched
            except subprocess.TimeoutExpired:
                # BarTender is still running - this is good for fast response
                app.logger.info(f"BarTender print job dispatched (background processing) - {copies} copies")
                return True  # Don't wait for completion
                
        except Exception as cli_error:
            print(f"Server: BarTender CLI method also failed: {cli_error}")
        return False
    except Exception as e:
        print(f"Server: BarTender print error: {e}")
        return False

def print_label(quotation, party, address='', phone='', mobile='', copies=1):
    """Print label using BarTender only - template required (with serialization for multiple copies)"""
    global BARTENDER_TEMPLATE
    
    try:
        # Check if BarTender template is configured
        if not BARTENDER_TEMPLATE:
            app.logger.error("BarTender template not configured")
            return False
            
        if not os.path.exists(BARTENDER_TEMPLATE):
            app.logger.error(f"BarTender template file not found: {BARTENDER_TEMPLATE}")
            return False
        
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
        
        # Print using BarTender (single invocation with serialization for multiple copies)
        if copies > 1:
            app.logger.info(f"Printing with BarTender template: {BARTENDER_TEMPLATE} ({copies} copies)")
        else:
            app.logger.info(f"Printing with BarTender template: {BARTENDER_TEMPLATE}")
        
        success = print_label_bartender(quotation, party_info, BARTENDER_TEMPLATE, copies)
        
        if success:
            if copies > 1:
                app.logger.info(f"BarTender print successful for quotation {quotation} ({copies} copies)")
            else:
                app.logger.info(f"BarTender print successful for quotation {quotation}")
            return True
        else:
            app.logger.error(f"BarTender print failed for quotation {quotation}")
            return False
        
    except Exception as e:
        app.logger.error(f"Print error: {e}")
        return False

def print_label_text(quotation, party_info, copy_number=None, total_copies=None):
    """Original text-based printing method (fallback)"""
    global SELECTED_PRINTER
    
    try:
        # Use the professional label formatting
        label_text = format_label(quotation, party_info, copy_number, total_copies)
        
        # Log which printer will be used
        printer_to_use = SELECTED_PRINTER if SELECTED_PRINTER else "Default System Printer"
        
        if copy_number is not None and total_copies is not None:
            print(f"Server: Text printing for quotation {quotation} (copy {copy_number} of {total_copies})")
        else:
            print(f"Server: Text printing for quotation {quotation}")
        
        print(f"Server: Target printer: {printer_to_use}")
        print(f"Label content:\n{label_text}")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt', mode='w', encoding='utf-8') as tf:
            tf.write(label_text)
            temp_file_name = tf.name

        # Optimized PowerShell Out-Printer method for fast printing
        try:
            if SELECTED_PRINTER:
                # Use specifically selected printer with optimized PowerShell command
                powershell_cmd = [
                    'powershell', 
                    '-WindowStyle', 'Hidden',
                    '-ExecutionPolicy', 'Bypass',
                    '-Command', 
                    f'Get-Content "{temp_file_name}" -Raw | Out-Printer -Name "{SELECTED_PRINTER}"'
                ]
                app.logger.info(f"Fast print to: {SELECTED_PRINTER}")
            else:
                # Use default printer with optimized command
                powershell_cmd = [
                    'powershell', 
                    '-WindowStyle', 'Hidden',
                    '-ExecutionPolicy', 'Bypass',
                    '-Command', 
                    f'Get-Content "{temp_file_name}" -Raw | Out-Printer'
                ]
                app.logger.info("Fast print to default printer")
            
            # Use Popen for non-blocking execution - don't wait for completion
            process = subprocess.Popen(powershell_cmd, 
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            
            # Set a very short timeout for immediate response
            try:
                stdout, stderr = process.communicate(timeout=2)  # 2 second max wait
                if process.returncode == 0:
                    app.logger.info(f"Print job dispatched successfully to {printer_to_use}")
                    success = True
                else:
                    app.logger.warning(f"Print dispatch warning: {stderr.decode() if stderr else 'Unknown error'}")
                    success = True  # Still consider success since job was dispatched
            except subprocess.TimeoutExpired:
                # Print job is still running - this is actually good for fast response
                app.logger.info(f"Print job dispatched (background processing) to {printer_to_use}")
                success = True  # Don't wait for completion
                
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
    """Handle print requests - BarTender only"""
    start_time = time.time()
    
    data = request.json
    if not data:
        return jsonify({'status': 'error', 'message': 'No data provided'})
    
    # Check if BarTender template is configured before proceeding
    if not BARTENDER_TEMPLATE:
        return jsonify({
            'status': 'error', 
            'message': 'BarTender template not configured. Please set template path in Settings.'
        })
    
    if not os.path.exists(BARTENDER_TEMPLATE):
        return jsonify({
            'status': 'error',
            'message': f'BarTender template file not found: {BARTENDER_TEMPLATE}'
        })
        
    quotation = data.get('quotation')
    party = data.get('party')
    address = data.get('address', '')
    phone = data.get('phone', '')
    mobile = data.get('mobile', '')
    copies = int(data.get('copies', 1))
    
    if not quotation or not party:
        return jsonify({'status': 'error', 'message': 'Quotation and party are required'})
    
    # Validate copies parameter
    if copies < 1:
        copies = 1
    elif copies > 100:
        return jsonify({'status': 'error', 'message': 'Maximum 100 copies allowed'})
    
    # Log with performance timing
    if copies > 1:
        app.logger.info(f"Print request received for quotation {quotation} ({copies} copies)")
    else:
        app.logger.info(f"Print request received for quotation {quotation}")
    
    # Try to print synchronously to catch errors
    try:
        success = print_label(quotation, party, address, phone, mobile, copies)
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Print job failed. Check BarTender template and printer configuration.',
                'quotation': quotation
            })
        
        # Record in database asynchronously
        def async_record():
            try:
                printed_db.record_print(quotation, party=party, address=address, phone=phone, mobile=mobile)
                app.logger.info(f"Recorded print job for quotation {quotation}")
            except Exception as e:
                app.logger.error(f"Failed to record print job: {e}")
        
        record_thread = threading.Thread(target=async_record, daemon=True)
        record_thread.start()
        
        # Return success response
        response_time = (time.time() - start_time) * 1000
        app.logger.info(f"Print request processed in {response_time:.2f}ms")
        
        if copies > 1:
            message = f'{copies} copies sent to printer successfully'
        else:
            message = 'Print job sent to printer successfully'
        
        return jsonify({
            'status': 'success', 
            'message': message,
            'quotation': quotation,
            'copies': copies,
            'response_time_ms': round(response_time, 2)
        })
        
    except Exception as e:
        app.logger.error(f"Print error: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Print job failed: {str(e)}',
            'quotation': quotation
        })

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

@app.route('/print-status', methods=['GET'])
def print_status():
    """Fast endpoint to check print queue status"""
    try:
        # Quick check of active print threads
        active_threads = threading.active_count()
        
        # Get recent print stats from database (last 10 prints)
        recent_prints = printed_db.get_recent(limit=10)
        
        return jsonify({
            'status': 'success',
            'active_threads': active_threads,
            'recent_prints_count': len(recent_prints.get('records', [])),
            'server_uptime': getattr(g, 'request_start_time', time.time()),
            'performance': 'optimized'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


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

@app.route('/check-updates', methods=['GET'])
def check_updates():
    """Check for available updates"""
    try:
        force = request.args.get('force', 'false').lower() == 'true'
        
        update_manager = UpdateManager()
        result = update_manager.check_and_update(force=force)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/install-update', methods=['POST'])
def install_update():
    """Manually install available update"""
    try:
        update_manager = UpdateManager()
        result = update_manager.manual_update()
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/update-config', methods=['GET', 'POST'])
def update_config():
    """Get or set update configuration"""
    try:
        update_manager = UpdateManager()
        
        if request.method == 'GET':
            return jsonify({
                'status': 'success',
                'config': update_manager.config,
                'current_version': update_manager.current_version
            })
        
        elif request.method == 'POST':
            data = request.json
            if not data:
                return jsonify({'status': 'error', 'message': 'No data provided'})
            
            # Update configuration
            for key, value in data.items():
                if key in update_manager.config:
                    update_manager.config[key] = value
            
            update_manager.save_update_config()
            
            return jsonify({
                'status': 'success',
                'message': 'Update configuration saved',
                'config': update_manager.config
            })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

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
    
    # Require BarTender template for printing functionality
    if not bartender_template:
        return jsonify({'success': False, 'error': 'BarTender template path is required'})
    
    # Validate BarTender template file exists
    if not os.path.exists(bartender_template):
        return jsonify({'success': False, 'error': f'BarTender template file not found: {bartender_template}'})
    
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
        
        # Connection successful, save all settings (bartender_template is now required)
        if save_db_settings(server, database, printer if printer else None, bartender_template):
            if printer:
                print(f"Server: Printer set to: {printer}")
                print(f"Server: All future print jobs will use: {printer}")
            else:
                print(f"Server: Printer selection cleared - will use default printer")
            
            print(f"Server: BarTender template configured: {bartender_template}")
            print(f"Server: BarTender template file exists: {os.path.exists(bartender_template)}")
                
            return jsonify({'success': True, 'message': 'Settings saved successfully. BarTender template configured.'})
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

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring and load balancers"""
    try:
        health_info = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'version': '1.0.0',
            'environment': Config.ENVIRONMENT,
            'uptime_seconds': int(time.time() - startup_time)
        }
        
        # Quick database connectivity test
        if DB_SERVER and DB_NAME:
            try:
                # Quick connection test with minimal timeout
                test_conn_str = f"DRIVER={{SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;Connection Timeout=5;"
                with pyodbc.connect(test_conn_str) as test_conn:
                    test_cursor = test_conn.cursor()
                    test_cursor.execute("SELECT 1")
                    test_cursor.fetchone()
                health_info['database'] = 'connected'
            except:
                health_info['database'] = 'disconnected'
                health_info['status'] = 'degraded'
        else:
            health_info['database'] = 'not_configured'
            health_info['status'] = 'degraded'
        
        # Check printed database
        try:
            # Test if printed_db module is accessible
            printed_db.init_db()  # This should be safe to call multiple times
            health_info['printed_db'] = 'connected'
        except Exception as e:
            health_info['printed_db'] = f'error: {str(e)}'
            health_info['status'] = 'degraded'
        
        status_code = 200 if health_info['status'] == 'healthy' else 503
        return jsonify(health_info), status_code
        
    except Exception as e:
        app.logger.error('Health check failed: %s', str(e), exc_info=True)
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 503

@app.route('/metrics')
def metrics():
    """Basic metrics endpoint for monitoring"""
    try:
        # Get log file sizes and counts
        log_dir = os.path.join(os.path.dirname(__file__), 'logs')
        log_files = {}
        if os.path.exists(log_dir):
            for filename in os.listdir(log_dir):
                if filename.endswith('.log'):
                    filepath = os.path.join(log_dir, filename)
                    try:
                        stat = os.stat(filepath)
                        log_files[filename] = {
                            'size_bytes': stat.st_size,
                            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        }
                    except:
                        pass
        
        metrics_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'application': {
                'name': 'Label Print Server',
                'version': '1.0.0',
                'environment': Config.ENVIRONMENT,
                'uptime_seconds': int(time.time() - startup_time)
            },
            'database': {
                'server': DB_SERVER,
                'database': DB_NAME,
                'configured': bool(DB_SERVER and DB_NAME)
            },
            'logs': log_files,
            'system': {
                'platform': os.name,
                'python_version': sys.version.split()[0]
            }
        }
        
        return jsonify(metrics_data)
        
    except Exception as e:
        app.logger.error('Metrics collection failed: %s', str(e), exc_info=True)
        return jsonify({'error': str(e)}), 500

# Record startup time for uptime calculation
startup_time = time.time()

# Initialize update system
def initialize_update_system():
    """Initialize the update management system"""
    global update_manager, update_checker
    try:
        update_manager = UpdateManager()
        update_checker = UpdateChecker(update_manager)
        update_checker.start()
        app.logger.info("Update system initialized successfully")
    except Exception as e:
        app.logger.error(f"Failed to initialize update system: {e}")

# Initialize update system on startup
initialize_update_system()

if __name__ == '__main__':
    # This will run when called directly (not as a service)
    print("Starting Label Print Server in development mode...")
    print("For production deployment, use the Windows service:")
    print("  python service.py install")
    print("  python service.py start")
    print("")
    app.run(host='0.0.0.0', port=5000, debug=True)