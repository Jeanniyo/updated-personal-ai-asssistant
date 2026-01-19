import os
import json
from datetime import datetime

# Data directory for JSON storage
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def _get_user_data_dir(user_id):
    """Get user-specific data directory"""
    user_dir = os.path.join(DATA_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def _read_json(filename, user_id=None):
    """Read JSON file from data directory"""
    if user_id:
        filepath = os.path.join(_get_user_data_dir(user_id), filename)
    else:
        filepath = os.path.join(DATA_DIR, filename)
    
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return None

def _write_json(filename, data, user_id=None):
    """Write JSON file to data directory"""
    if user_id:
        filepath = os.path.join(_get_user_data_dir(user_id), filename)
    else:
        filepath = os.path.join(DATA_DIR, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def init_db(user_id=None):
    """Initialize JSON data files for a user"""
    # Initialize empty data files if they don't exist
    if _read_json('agenda.json', user_id) is None:
        _write_json('agenda.json', [], user_id)
    if _read_json('diary.json', user_id) is None:
        _write_json('diary.json', [], user_id)
    if _read_json('chat_history.json', user_id) is None:
        _write_json('chat_history.json', [], user_id)
    if _read_json('profile.json', user_id) is None:
        _write_json('profile.json', {'name': 'User', 'photo_path': None}, user_id)
    if _read_json('daily_tips.json', user_id) is None:
        _write_json('daily_tips.json', [], user_id)
    if _read_json('attachments.json', user_id) is None:
        _write_json('attachments.json', [], user_id)

def migrate_existing_data_to_user(user_id):
    """Migrate existing data from root data directory to user directory"""
    files_to_migrate = [
        'agenda.json', 'diary.json', 'chat_history.json', 
        'profile.json', 'daily_tips.json', 'attachments.json'
    ]
    
    user_dir = _get_user_data_dir(user_id)
    migrated = False
    
    for filename in files_to_migrate:
        old_path = os.path.join(DATA_DIR, filename)
        new_path = os.path.join(user_dir, filename)
        
        # Only migrate if old file exists and new file doesn't
        if os.path.exists(old_path) and not os.path.exists(new_path):
            with open(old_path, 'r') as f:
                data = json.load(f)
            with open(new_path, 'w') as f:
                json.dump(data, f, indent=2)
            migrated = True
    
    if migrated:
        print(f"Migrated existing data to user {user_id}")
    
    return migrated

# --- Agenda ---
def add_agenda(content, date=None, user_id=None):
    agenda_list = _read_json('agenda.json', user_id) or []
    new_item = {
        'id': len(agenda_list) + 1,
        'content': content,
        'date': date,
        'timestamp': datetime.now().isoformat()
    }
    agenda_list.append(new_item)
    _write_json('agenda.json', agenda_list, user_id)
    return new_item['id']

def update_agenda(id, content, date, user_id=None):
    agenda_list = _read_json('agenda.json', user_id) or []
    for item in agenda_list:
        if item['id'] == id:
            item['content'] = content
            item['date'] = date
            break
    _write_json('agenda.json', agenda_list, user_id)

def delete_agenda(id, user_id=None):
    agenda_list = _read_json('agenda.json', user_id) or []
    agenda_list = [item for item in agenda_list if item['id'] != id]
    _write_json('agenda.json', agenda_list, user_id)
    
    # Also delete attachments
    attachments = _read_json('attachments.json', user_id) or []
    attachments = [att for att in attachments if not (att['parent_type'] == 'agenda' and att['parent_id'] == id)]
    _write_json('attachments.json', attachments, user_id)

def get_agenda(user_id=None):
    agenda_list = _read_json('agenda.json', user_id) or []
    return sorted(agenda_list, key=lambda x: x.get('timestamp', ''), reverse=True)

# --- Diary ---
def add_diary(content, user_id=None):
    diary_list = _read_json('diary.json', user_id) or []
    new_item = {
        'id': len(diary_list) + 1,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    diary_list.append(new_item)
    _write_json('diary.json', diary_list, user_id)
    return new_item['id']

def update_diary(id, content, user_id=None):
    diary_list = _read_json('diary.json', user_id) or []
    for item in diary_list:
        if item['id'] == id:
            item['content'] = content
            break
    _write_json('diary.json', diary_list, user_id)

def delete_diary(id, user_id=None):
    diary_list = _read_json('diary.json', user_id) or []
    diary_list = [item for item in diary_list if item['id'] != id]
    _write_json('diary.json', diary_list, user_id)
    
    # Also delete attachments
    attachments = _read_json('attachments.json', user_id) or []
    attachments = [att for att in attachments if not (att['parent_type'] == 'diary' and att['parent_id'] == id)]
    _write_json('attachments.json', attachments, user_id)

def get_diary(user_id=None):
    diary_list = _read_json('diary.json', user_id) or []
    return sorted(diary_list, key=lambda x: x.get('timestamp', ''), reverse=True)

# --- Chats ---
def add_chat(role, content, user_id=None):
    chat_history = _read_json('chat_history.json', user_id) or []
    new_message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    chat_history.append(new_message)
    _write_json('chat_history.json', chat_history, user_id)

def get_chats(limit=50, user_id=None):
    chat_history = _read_json('chat_history.json', user_id) or []
    return chat_history[-limit:] if len(chat_history) > limit else chat_history

# --- Profile ---
def get_profile(user_id=None):
    profile = _read_json('profile.json', user_id)
    if profile:
        return profile
    return {'name': 'User', 'photo_path': None}

def update_profile(name, photo_path=None, user_id=None):
    profile = get_profile(user_id)
    profile['name'] = name
    if photo_path:
        profile['photo_path'] = photo_path
    _write_json('profile.json', profile, user_id)

# --- Attachments ---
def add_attachment(parent_type, parent_id, file_path, original_name, media_type, user_id=None):
    attachments = _read_json('attachments.json', user_id) or []
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
    _write_json('attachments.json', attachments, user_id)

def get_attachments(parent_type, parent_id, user_id=None):
    attachments = _read_json('attachments.json', user_id) or []
    return [att for att in attachments if att['parent_type'] == parent_type and att['parent_id'] == parent_id]

def get_all_attachments(user_id=None):
    attachments = _read_json('attachments.json', user_id) or []
    return sorted(attachments, key=lambda x: x.get('timestamp', ''), reverse=True)

def delete_attachment(id, user_id=None):
    attachments = _read_json('attachments.json', user_id) or []
    attachments = [att for att in attachments if att['id'] != id]
    _write_json('attachments.json', attachments, user_id)

# --- Daily Tips ---
def add_daily_tip(content, category='General', user_id=None):
    tips = _read_json('daily_tips.json', user_id) or []
    today = datetime.now().strftime('%Y-%m-%d')
    new_tip = {
        'id': len(tips) + 1,
        'content': content,
        'category': category,
        'date': today,
        'timestamp': datetime.now().isoformat()
    }
    tips.append(new_tip)
    _write_json('daily_tips.json', tips, user_id)
    return new_tip['id']

def get_daily_tip(user_id=None):
    """Get today's tip, or return None if no tip exists for today"""
    tips = _read_json('daily_tips.json', user_id) or []
    today = datetime.now().strftime('%Y-%m-%d')
    today_tips = [tip for tip in tips if tip['date'] == today]
    return today_tips[-1] if today_tips else None

def get_all_tips(user_id=None):
    tips = _read_json('daily_tips.json', user_id) or []
    return sorted(tips, key=lambda x: x.get('timestamp', ''), reverse=True)
