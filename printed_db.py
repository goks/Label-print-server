import sqlite3
import os
from datetime import datetime, timezone

DB_FILE = os.path.join(os.path.dirname(__file__), 'printed_records.db')

def init_db():
    """Initialize the SQLite database and table if not exists."""
    conn = sqlite3.connect(DB_FILE)
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
        conn.commit()
    finally:
        conn.close()

def record_print(quotation, party=None, address=None, phone=None, mobile=None):
    """Record a printed quotation entry."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO printed (quotation, party, address, phone, mobile, printed_at) VALUES (?, ?, ?, ?, ?, ?)',
            (str(quotation), party, address, phone, mobile, datetime.now().isoformat())
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_recent(limit=100, q=None, offset=0):
    conn = sqlite3.connect(DB_FILE)
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
    finally:
        conn.close()
