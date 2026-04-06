import sqlite3
import logging

def init_db(db_path='deals.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS listings_seen (
            listing_id TEXT PRIMARY KEY,
            platform TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def is_seen(listing_id, db_path='deals.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM listings_seen WHERE listing_id = ?', (listing_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def mark_as_seen(listing_id, platform, db_path='deals.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO listings_seen (listing_id, platform) 
            VALUES (?, ?)
        ''', (listing_id, platform))
        conn.commit()
    except sqlite3.IntegrityError:
        pass  # Already exists
    finally:
        conn.close()
