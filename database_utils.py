from datetime import datetime
from google_drive_client import get_drive_client

# Initialize Google Drive client
drive = None

def init_db():
    """Initialize Google Drive connection and setup folders"""
    global drive
    drive = get_drive_client()
    
    # Initialize empty data files if they don't exist
    if drive.read_json_file('agenda.json') is None:
        drive.write_json_file('agenda.json', [])
    if drive.read_json_file('diary.json') is None:
        drive.write_json_file('diary.json', [])
    if drive.read_json_file('chat_history.json') is None:
        drive.write_json_file('chat_history.json', [])
    if drive.read_json_file('profile.json') is None:
        drive.write_json_file('profile.json', {'name': 'User', 'photo_path': None})
    if drive.read_json_file('daily_tips.json') is None:
        drive.write_json_file('daily_tips.json', [])
    if drive.read_json_file('attachments.json') is None:
        drive.write_json_file('attachments.json', [])

# --- Agenda ---
def add_agenda(content, date=None):
    agenda_list = drive.read_json_file('agenda.json') or []
    new_item = {
        'id': len(agenda_list) + 1,
        'content': content,
        'date': date,
        'timestamp': datetime.now().isoformat()
    }
    agenda_list.append(new_item)
    drive.write_json_file('agenda.json', agenda_list)
    return new_item['id']

def update_agenda(id, content, date):
    agenda_list = drive.read_json_file('agenda.json') or []
    for item in agenda_list:
        if item['id'] == id:
            item['content'] = content
            item['date'] = date
            break
    drive.write_json_file('agenda.json', agenda_list)

def delete_agenda(id):
    agenda_list = drive.read_json_file('agenda.json') or []
    agenda_list = [item for item in agenda_list if item['id'] != id]
    drive.write_json_file('agenda.json', agenda_list)
    
    # Also delete attachments
    attachments = drive.read_json_file('attachments.json') or []
    attachments = [att for att in attachments if not (att['parent_type'] == 'agenda' and att['parent_id'] == id)]
    drive.write_json_file('attachments.json', attachments)

def get_agenda():
    agenda_list = drive.read_json_file('agenda.json') or []
    return sorted(agenda_list, key=lambda x: x.get('timestamp', ''), reverse=True)

# --- Diary ---
def add_diary(content):
    diary_list = drive.read_json_file('diary.json') or []
    new_item = {
        'id': len(diary_list) + 1,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    diary_list.append(new_item)
    drive.write_json_file('diary.json', diary_list)
    return new_item['id']

def update_diary(id, content):
    diary_list = drive.read_json_file('diary.json') or []
    for item in diary_list:
        if item['id'] == id:
            item['content'] = content
            break
    drive.write_json_file('diary.json', diary_list)

def delete_diary(id):
    diary_list = drive.read_json_file('diary.json') or []
    diary_list = [item for item in diary_list if item['id'] != id]
    drive.write_json_file('diary.json', diary_list)
    
    # Also delete attachments
    attachments = drive.read_json_file('attachments.json') or []
    attachments = [att for att in attachments if not (att['parent_type'] == 'diary' and att['parent_id'] == id)]
    drive.write_json_file('attachments.json', attachments)

def get_diary():
    diary_list = drive.read_json_file('diary.json') or []
    return sorted(diary_list, key=lambda x: x.get('timestamp', ''), reverse=True)

# --- Chats ---
def add_chat(role, content):
    chat_history = drive.read_json_file('chat_history.json') or []
    new_message = {
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    }
    chat_history.append(new_message)
    drive.write_json_file('chat_history.json', chat_history)

def get_chats(limit=50):
    chat_history = drive.read_json_file('chat_history.json') or []
    return chat_history[-limit:] if len(chat_history) > limit else chat_history

# --- Profile ---
def get_profile():
    profile = drive.read_json_file('profile.json')
    if profile:
        return profile
    return {'name': 'User', 'photo_path': None}

def update_profile(name, photo_path=None):
    profile = get_profile()
    profile['name'] = name
    if photo_path:
        profile['photo_path'] = photo_path
    drive.write_json_file('profile.json', profile)

# --- Attachments ---
def add_attachment(parent_type, parent_id, file_path, original_name, media_type):
    attachments = drive.read_json_file('attachments.json') or []
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
    drive.write_json_file('attachments.json', attachments)

def get_attachments(parent_type, parent_id):
    attachments = drive.read_json_file('attachments.json') or []
    return [att for att in attachments if att['parent_type'] == parent_type and att['parent_id'] == parent_id]

def get_all_attachments():
    attachments = drive.read_json_file('attachments.json') or []
    return sorted(attachments, key=lambda x: x.get('timestamp', ''), reverse=True)

def delete_attachment(id):
    attachments = drive.read_json_file('attachments.json') or []
    attachments = [att for att in attachments if att['id'] != id]
    drive.write_json_file('attachments.json', attachments)

# --- Daily Tips ---
def add_daily_tip(content, category='General'):
    tips = drive.read_json_file('daily_tips.json') or []
    today = datetime.now().strftime('%Y-%m-%d')
    new_tip = {
        'id': len(tips) + 1,
        'content': content,
        'category': category,
        'date': today,
        'timestamp': datetime.now().isoformat()
    }
    tips.append(new_tip)
    drive.write_json_file('daily_tips.json', tips)
    return new_tip['id']

def get_daily_tip():
    """Get today's tip, or return None if no tip exists for today"""
    tips = drive.read_json_file('daily_tips.json') or []
    today = datetime.now().strftime('%Y-%m-%d')
    today_tips = [tip for tip in tips if tip['date'] == today]
    return today_tips[-1] if today_tips else None

def get_all_tips():
    tips = drive.read_json_file('daily_tips.json') or []
    return sorted(tips, key=lambda x: x.get('timestamp', ''), reverse=True)
