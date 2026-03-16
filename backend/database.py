import sqlite3
import os
from config import Config

def get_db():
    """Get a database connection."""
    db = sqlite3.connect(Config.DATABASE_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db():
    """Initialize the database with schema."""
    db = get_db()
    cursor = db.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT,
            full_name TEXT NOT NULL,
            age INTEGER,
            country TEXT,
            blood_group TEXT,
            phone TEXT,
            phone_country_code TEXT,
            emergency_contact_1 TEXT,
            emergency_contact_1_code TEXT,
            emergency_contact_2 TEXT,
            emergency_contact_2_code TEXT,
            emergency_contact_3 TEXT,
            emergency_contact_3_code TEXT,
            auth_provider TEXT DEFAULT 'email',
            google_id TEXT,
            profile_photo TEXT,
            last_known_lat REAL,
            last_known_lng REAL,
            last_location_update TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            last_login TEXT DEFAULT (datetime('now'))
        )
    ''')

    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            description TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_km REAL NOT NULL DEFAULT 10,
            severity TEXT DEFAULT 'warning',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    # Notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_done INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    # Danger zones table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS danger_zones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            radius_km REAL NOT NULL,
            severity TEXT DEFAULT 'high',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    # Documents table (metadata only - files stored encrypted on disk)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER,
            category TEXT DEFAULT 'other',
            uploaded_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Emergency SOS logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emergency_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            status TEXT DEFAULT 'active',
            resolved_at TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Activity logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            ip_address TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    ''')

    # Blockchain blocks
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS blockchain_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_index INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            data TEXT NOT NULL,
            data_hash TEXT NOT NULL,
            previous_hash TEXT NOT NULL,
            nonce INTEGER DEFAULT 0
        )
    ''')

    # User alert read status
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_alert_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            alert_id INTEGER,
            notification_id INTEGER,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    db.commit()
    db.close()
    print("✅ Database initialized successfully!")

if __name__ == '__main__':
    init_db()
