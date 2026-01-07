import sqlite3
import os
from datetime import datetime

# SQLite DB file
DB_NAME = os.path.join(os.path.dirname(__file__), "assistant_local.db")

# Initialize DB and tables
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Agenda table
    c.execute('''
        CREATE TABLE IF NOT EXISTS agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            date TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Diary table
    c.execute('''
        CREATE TABLE IF NOT EXISTS diary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Chat table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Profile table
    c.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT DEFAULT 'User',
            photo_path TEXT
        )
    ''')
    
    # Attachments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_type TEXT NOT NULL,
            parent_id INTEGER NOT NULL,
            file_path TEXT NOT NULL,
            original_name TEXT,
            media_type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Daily tips table
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            date TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Initialize profile if empty
    c.execute("SELECT count(*) FROM profile")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO profile (name) VALUES ('User')")
    
    conn.commit()
    conn.close()

# --- Agenda ---
def add_agenda(content, date=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO agenda (content, date) VALUES (?, ?)", (content, date))
    agenda_id = c.lastrowid
    conn.commit()
    conn.close()
    return agenda_id

def update_agenda(id, content, date):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE agenda SET content = ?, date = ? WHERE id = ?", (content, date, id))
    conn.commit()
    conn.close()

def delete_agenda(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM agenda WHERE id = ?", (id,))
    c.execute("DELETE FROM attachments WHERE parent_type = 'agenda' AND parent_id = ?", (id,))
    conn.commit()
    conn.close()

def get_agenda():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, content, date, timestamp FROM agenda ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "content": r[1], "date": r[2], "timestamp": r[3]} for r in rows]

# --- Diary ---
def add_diary(content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO diary (content) VALUES (?)", (content,))
    diary_id = c.lastrowid
    conn.commit()
    conn.close()
    return diary_id

def update_diary(id, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE diary SET content = ? WHERE id = ?", (content, id))
    conn.commit()
    conn.close()

def delete_diary(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM diary WHERE id = ?", (id,))
    c.execute("DELETE FROM attachments WHERE parent_type = 'diary' AND parent_id = ?", (id,))
    conn.commit()
    conn.close()

def get_diary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, content, timestamp FROM diary ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

# --- Chats ---
def add_chat(role, content):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO chats (role, content) VALUES (?, ?)", (role, content))
    conn.commit()
    conn.close()

def get_chats(limit=50):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT role, content, timestamp FROM chats ORDER BY timestamp ASC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1], "timestamp": r[2]} for r in rows]

# --- Profile ---
def get_profile():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, photo_path FROM profile LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {"name": row[0], "photo_path": row[1]}
    return {"name": "User", "photo_path": None}

def update_profile(name, photo_path=None):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    if photo_path:
        c.execute("UPDATE profile SET name = ?, photo_path = ?", (name, photo_path))
    else:
        c.execute("UPDATE profile SET name = ?", (name,))
    conn.commit()
    conn.close()

# --- Attachments ---
def add_attachment(parent_type, parent_id, file_path, original_name, media_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO attachments (parent_type, parent_id, file_path, original_name, media_type) VALUES (?, ?, ?, ?, ?)",
              (parent_type, parent_id, file_path, original_name, media_type))
    conn.commit()
    conn.close()

def get_attachments(parent_type, parent_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_path, original_name, media_type FROM attachments WHERE parent_type = ? AND parent_id = ?",
              (parent_type, parent_id))
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "file_path": r[1], "original_name": r[2], "media_type": r[3]} for r in rows]

def get_all_attachments():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, file_path, original_name, media_type, timestamp FROM attachments ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "file_path": r[1], "original_name": r[2], "media_type": r[3], "timestamp": r[4]} for r in rows]

def delete_attachment(id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM attachments WHERE id = ?", (id,))
    conn.commit()
    conn.close()

# --- Daily Tips ---
def add_daily_tip(content, category='General'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("INSERT INTO daily_tips (content, category, date) VALUES (?, ?, ?)", (content, category, today))
    tip_id = c.lastrowid
    conn.commit()
    conn.close()
    return tip_id

def get_daily_tip():
    """Get today's tip, or return None if no tip exists for today"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT id, content, category, date, timestamp FROM daily_tips WHERE date = ? ORDER BY timestamp DESC LIMIT 1", (today,))
    row = c.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "content": row[1], "category": row[2], "date": row[3], "timestamp": row[4]}
    return None

def get_all_tips():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id, content, category, date, timestamp FROM daily_tips ORDER BY timestamp DESC")
    rows = c.fetchall()
    conn.close()
    return [{"id": r[0], "content": r[1], "category": r[2], "date": r[3], "timestamp": r[4]} for r in rows]

