import os
import json
from datetime import datetime

# Data directory for JSON storage
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def _read_json(filename):
    """Read JSON file from data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def _write_json(filename, data):
    """Write JSON file to data directory"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def init_db():
    """Initialize JSON data files"""
    # Initialize empty data files if they don't exist
    if _read_json('agenda.json') is None:
        _write_json('agenda.json', [])
    if _read_json('diary.json') is None:
        _write_json('diary.json', [])
    if _read_json('chat_history.json') is None:
        _write_json('chat_history.json', [])
    if _read_json('profile.json') is None:
        _write_json('profile.json', {'name': 'User', 'photo_path': None})
    if _read_json('daily_tips.json') is None:
        _write_json('daily_tips.json', [])
    if _read_json('attachments.json') is None:
        _write_json('attachments.json', [])

# --- Agenda ---
def add_agenda(content, date=None):
    agenda_list = _read_json('agenda.json') or []
    new_item = {
        'id': len(agenda_list) + 1,
        'content': content,
        'date': date,
        'timestamp': datetime.now().isoformat()
    }
    agenda_list.append(new_item)
    _write_json('agenda.json', agenda_list)
    return new_item['id']

def update_agenda(id, content, date):
    agenda_list = _read_json('agenda.json') or []
    for item in agenda_list:
        if item['id'] == id:
            item['content'] = content
            item['date'] = date
            break
    _write_json('agenda.json', agenda_list)

def delete_agenda(id):
    agenda_list = _read_json('agenda.json') or []
    agenda_list = [item for item in agenda_list if item['id'] != id]
    _write_json('agenda.json', agenda_list)
    
    # Also delete attachments
    attachments = _read_json('attachments.json') or []
    attachments = [att for att in attachments if not (att['parent_type'] == 'agenda' and att['parent_id'] == id)]
    _write_json('attachments.json', attachments)

def get_agenda():
    agenda_list = _read_json('agenda.json') or []
    return sorted(agenda_list, key=lambda x: x.get('timestamp', ''), reverse=True)

# --- Diary ---
def add_diary(content):
    diary_list = _read_json('diary.json') or []
    new_item = {
        'id': len(diary_list) + 1,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    diary_list.append(new_item)
    _write_json('diary.json', diary_list)
    return new_item['id']

def update_diary(id, content):
    diary_list = _read_json('diary.json') or []
    for item in diary_list:
        if item['id'] == id:
            item['content'] = content
            break
    _write_json('diary.json', diary_list)

def delete_diary(id):
    diary_list = _read_json('diary.json') or []
    diary_list = [item for item in diary_list if item['id'] != id]
    _write_json('diary.json', diary_list)
    
    # Also delete attachments
    attachments = _read_json('attachments.json') or []
    attachments = [att for att in attachments if not (att['parent_type'] == 'diary' and att['parent_id'] == id)]
    _write_json('attachments.json', attachments)

def get_diary():
    diary_list = _read_json('diary.json') or []
    return sorted(diary_list, key=lambda x: x.get('timestamp', ''), reverse=True)

# --- Chats ---
def add_chat(role, content):
    chat_history = _read_json('chat_history.json') or []
    new_message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    chat_history.append(new_message)
    _write_json('chat_history.json', chat_history)

def get_chats(limit=50):
    chat_history = _read_json('chat_history.json') or []
    return chat_history[-limit:] if len(chat_history) > limit else chat_history

# --- Profile ---
def get_profile():
    profile = _read_json('profile.json')
    if profile:
        return profile
    return {'name': 'User', 'photo_path': None}

def update_profile(name, photo_path=None):
    profile = get_profile()
    profile['name'] = name
    if photo_path:
        profile['photo_path'] = photo_path
    _write_json('profile.json', profile)

# --- Attachments ---
def add_attachment(parent_type, parent_id, file_path, original_name, media_type):
    attachments = _read_json('attachments.json') or []
    new_attachment = {
        'id': len(attachments) + 1,
        'parent_type': parent_type,
        'parent_id': parent_id,
        'file_path': file_path,
        'original_name': original_name,
        'media_type': media_type,
        'timestamp': datetime.now().isoformat()
    }
    attachments.append(new_attachment)
    _write_json('attachments.json', attachments)

def get_attachments(parent_type, parent_id):
    attachments = _read_json('attachments.json') or []
    return [att for att in attachments if att['parent_type'] == parent_type and att['parent_id'] == parent_id]

def get_all_attachments():
    attachments = _read_json('attachments.json') or []
    return sorted(attachments, key=lambda x: x.get('timestamp', ''), reverse=True)

def delete_attachment(id):
    attachments = _read_json('attachments.json') or []
    attachments = [att for att in attachments if att['id'] != id]
    _write_json('attachments.json', attachments)

# --- Daily Tips ---
def add_daily_tip(content, category='General'):
    tips = _read_json('daily_tips.json') or []
    today = datetime.now().strftime('%Y-%m-%d')
    new_tip = {
        'id': len(tips) + 1,
        'content': content,
        'category': category,
        'date': today,
        'timestamp': datetime.now().isoformat()
    }
    tips.append(new_tip)
    _write_json('daily_tips.json', tips)
    return new_tip['id']

def get_daily_tip():
    """Get today's tip, or return None if no tip exists for today"""
    tips = _read_json('daily_tips.json') or []
    today = datetime.now().strftime('%Y-%m-%d')
    today_tips = [tip for tip in tips if tip['date'] == today]
    return today_tips[-1] if today_tips else None

def get_all_tips():
    tips = _read_json('daily_tips.json') or []
    return sorted(tips, key=lambda x: x.get('timestamp', ''), reverse=True)
