import sqlite3
import os
import threading
from datetime import datetime, timezone

# Use AppData for database when installed in Program Files
app_dir = os.path.dirname(__file__)
if 'Program Files' in app_dir:
    # Running from installation - use user's AppData
    data_dir = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~')), 
                           'LabelPrintServer', 'data')
    os.makedirs(data_dir, exist_ok=True)
    DB_FILE = os.path.join(data_dir, 'printed_records.db')
else:
    # Running from development directory
    DB_FILE = os.path.join(app_dir, 'printed_records.db')

# Thread-local storage for database connections
_thread_local = threading.local()

def _get_connection():
    """Get a thread-local database connection (connection reuse per thread)"""
    if not hasattr(_thread_local, 'connection') or _thread_local.connection is None:
        _thread_local.connection = sqlite3.connect(DB_FILE, check_same_thread=False)
        _thread_local.connection.row_factory = sqlite3.Row
    return _thread_local.connection

def init_db():
    """Initialize the SQLite database and table if not exists."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS printed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation TEXT NOT NULL,
                party TEXT,
                address TEXT,
                phone TEXT,
                mobile TEXT,
                printed_at TEXT NOT NULL
            )
        ''')
        # Create index for faster searches
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_quotation ON printed(quotation)
        ''')
        cur.execute('''
            CREATE INDEX IF NOT EXISTS idx_printed_at ON printed(printed_at DESC)
        ''')
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise

def record_print(quotation, party=None, address=None, phone=None, mobile=None):
    """Record a printed quotation entry."""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO printed (quotation, party, address, phone, mobile, printed_at) VALUES (?, ?, ?, ?, ?, ?)',
            (str(quotation), party, address, phone, mobile, datetime.now().isoformat())
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        raise

def get_recent(limit=100, q=None, offset=0):
    """Get recent printed records with optimized query"""
    conn = _get_connection()
    try:
        cur = conn.cursor()
        if q:
            like = f"%{q}%"
            # total matching count first
            cur.execute('SELECT COUNT(*) FROM printed WHERE quotation LIKE ? OR party LIKE ? OR address LIKE ?', (like, like, like))
            total = cur.fetchone()[0]
            # then fetch page rows
            cur.execute(
                'SELECT id, quotation, party, address, phone, mobile, printed_at FROM printed WHERE quotation LIKE ? OR party LIKE ? OR address LIKE ? ORDER BY id DESC LIMIT ? OFFSET ?',
                (like, like, like, limit, offset)
            )
        else:
            # total count
            cur.execute('SELECT COUNT(*) FROM printed')
            total = cur.fetchone()[0]
            # then fetch page rows
            cur.execute('SELECT id, quotation, party, address, phone, mobile, printed_at FROM printed ORDER BY id DESC LIMIT ? OFFSET ?', (limit, offset))

        rows = cur.fetchall()
        result = [
            {
                'id': r[0],
                'quotation': r[1],
                'party': r[2],
                'address': r[3],
                'phone': r[4],
                'mobile': r[5],
                'printed_at': r[6]
            }
            for r in rows
        ]
        return {'total': total, 'records': result}
    except Exception as e:
        raise

