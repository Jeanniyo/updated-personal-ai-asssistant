import http.server
import socketserver
import json
import os
import mimetypes
import base64
import uuid
import time
from collections import defaultdict
from database_utils import (
    init_db, add_agenda, add_diary, get_agenda, get_diary, add_chat, get_chats,
    update_agenda, delete_agenda, update_diary, delete_diary, get_profile,
    update_profile, add_attachment, get_attachments, get_all_attachments, delete_attachment,
    add_daily_tip, get_daily_tip, get_all_tips, migrate_existing_data_to_user
)
from gemini_client import generate_content
from auth_utils import (
    init_users_db, register_user, login_user, verify_token, create_default_user
)

PORT = int(os.environ.get('PORT', 8000))
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'dist')
UPLOADS_DIR = os.path.join(PUBLIC_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Helper function to get user from request
def get_user_from_token(auth_header):
    """Extract and verify user from Authorization header"""
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header.split(' ')[1]
    success, user_data = verify_token(token)
    if success:
        return user_data
    return None

# --- Request Monitoring ---
class RequestMonitor:
    def __init__(self):
        self.requests = defaultdict(list)
        self.threshold = 50  # max requests per window
        self.window = 10  # seconds

    def track(self, path):
        now = time.time()
        self.requests[path] = [t for t in self.requests[path] if t > now - self.window]
        self.requests[path].append(now)
        count = len(self.requests[path])
        if count == self.threshold:
            print(f"\033[91m[WARNING] High traffic detected on {path}: {count} requests in last {self.window}s\033[0m")
        elif count > self.threshold and count % 10 == 0:
            print(f"\033[91m[WARNING] CONTINUED High traffic on {path}: {count} requests\033[0m")

monitor = RequestMonitor()

# --- Request Handler ---
class RequestHandler(http.server.SimpleHTTPRequestHandler):

    def log_message(self, format, *args):
        # Only log non-static failures and API requests
        is_static = any(self.path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.ico', '.svg', '.woff2'])
        
        # Determine status code based on format string or args length
        # log_request sends: request_line, code, size
        # log_error sends: code, message
        status_code = 200
        try:
            if len(args) == 3: # Likely log_request
                status_code = int(args[1])
            elif len(args) == 2: # Likely log_error
                status_code = int(args[0])
        except (ValueError, TypeError):
            pass
            
        is_success = status_code < 400
        monitor.track(self.path)
        if not (is_static and is_success):
            super().log_message(format, *args)

    # --- GET ---
    def do_GET(self):
        # Public auth endpoint
        if self.path == '/api/auth/verify':
            auth_header = self.headers.get('Authorization')
            user = get_user_from_token(auth_header)
            if user:
                self.send_json({'authenticated': True, 'user': user})
            else:
                self.send_json({'authenticated': False}, status=401)
            return
        
        # Protected API Endpoints - require authentication
        auth_header = self.headers.get('Authorization')
        user = get_user_from_token(auth_header)
        
        if not user and self.path.startswith('/api/'):
            self.send_json({'error': 'Unauthorized'}, status=401)
            return
        
        user_id = user['id'] if user else None
        
        if self.path == '/api/agenda':
            self.send_json(get_agenda_with_attachments('agenda', user_id))
            return
        if self.path == '/api/diary':
            self.send_json(get_agenda_with_attachments('diary', user_id))
            return
        if self.path == '/api/chat/history':
            self.send_json(get_chats(user_id=user_id))
            return
        if self.path == '/api/profile':
            self.send_json(get_profile(user_id))
            return
        if self.path == '/api/files':
            self.send_json(get_all_attachments(user_id))
            return
        if self.path == '/api/daily-tip':
            tip = get_daily_tip(user_id)
            if tip:
                self.send_json(tip)
            else:
                # Generate a new tip if none exists for today
                self.generate_daily_tip(user_id)
            return

        # Serve uploaded files
        if self.path.startswith('/uploads/'):
            file_path = os.path.join(PUBLIC_DIR, self.path.lstrip('/'))
            if os.path.exists(file_path):
                self.send_file(file_path)
            else:
                self.send_error(404, "File not found")
            return

        # Serve static React files
        if self.path == '/':
            self.path = '/index.html'
        file_path = os.path.join(PUBLIC_DIR, self.path.lstrip('/'))
        print(f"[DEBUG] Requested: {self.path} -> Resolved: {file_path} -> Exists: {os.path.exists(file_path)}")
        if not os.path.exists(file_path) and not self.path.startswith('/api'):
            file_path = os.path.join(PUBLIC_DIR, 'index.html')
        if os.path.exists(file_path) and os.path.isfile(file_path):
            self.send_file(file_path)
        else:
            self.send_error(404, "File not found")

    # --- POST ---
    def do_POST(self):
        # Public auth endpoints
        if self.path == '/api/auth/register':
            self.handle_register()
            return
        if self.path == '/api/auth/login':
            self.handle_login()
            return
        
        # Protected endpoints - require authentication
        auth_header = self.headers.get('Authorization')
        user = get_user_from_token(auth_header)
        
        if not user:
            self.send_json({'error': 'Unauthorized'}, status=401)
            return
        
        if self.path == '/api/chat':
            self.handle_chat(user['id'])
            return
        if self.path == '/api/profile':
            self.handle_profile(user['id'])
            return
        if self.path == '/api/upload':
            self.handle_upload(user['id'])
            return
        if self.path == '/api/attachment':
            self.handle_attachment(user['id'])
            return
        if self.path == '/api/daily-tip/generate':
            self.generate_daily_tip(user['id'])
            return
        self.send_error(404)

    # --- PUT ---
    def do_PUT(self):
        auth_header = self.headers.get('Authorization')
        user = get_user_from_token(auth_header)
        
        if not user:
            self.send_json({'error': 'Unauthorized'}, status=401)
            return
        
        if self.path == '/api/agenda':
            self.handle_update_agenda(user['id'])
            return
        if self.path == '/api/diary':
            self.handle_update_diary(user['id'])
            return
        self.send_error(404)

    # --- DELETE ---
    def do_DELETE(self):
        auth_header = self.headers.get('Authorization')
        user = get_user_from_token(auth_header)
        
        if not user:
            self.send_json({'error': 'Unauthorized'}, status=401)
            return
        
        if self.path == '/api/agenda':
            self.handle_delete_agenda(user['id'])
            return
        if self.path == '/api/diary':
            self.handle_delete_diary(user['id'])
            return
        if self.path == '/api/files':
            self.handle_delete_attachment(user['id'])
            return
        self.send_error(404)

    # --- Helpers ---
    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_file(self, file_path):
        self.send_response(200)
        mime_type, _ = mimetypes.guess_type(file_path)
        self.send_header('Content-type', mime_type or 'application/octet-stream')
        self.end_headers()
        with open(file_path, 'rb') as f:
            self.wfile.write(f.read())

    def read_json(self):
        content_length = int(self.headers['Content-Length'])
        return json.loads(self.rfile.read(content_length))

    # --- POST helpers ---
    def handle_register(self):
        """Handle user registration"""
        data = self.read_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        success, message, user_id = register_user(username, password)
        
        if success:
            # Initialize user database
            init_db(user_id)
            # Auto-login after registration
            success, msg, token, user_data = login_user(username, password)
            self.send_json({'success': True, 'token': token, 'user': user_data})
        else:
            self.send_json({'success': False, 'error': message}, status=400)
    
    def handle_login(self):
        """Handle user login"""
        data = self.read_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        success, message, token, user_data = login_user(username, password)
        
        if success:
            self.send_json({'success': True, 'token': token, 'user': user_data})
        else:
            self.send_json({'success': False, 'error': message}, status=401)
    
    
    def handle_chat(self, user_id):
        data = self.read_json()
        user_message = data.get('message', '')
        add_chat('user', user_message, user_id)

        system_prompt = f"""You are an intelligent and friendly personal AI assistant. You help users with:
1. Managing their agenda and schedule
2. Recording diary entries and thoughts
3. Answering questions and having conversations
4. Providing helpful advice and information

Analyze the user's message and determine if it's:
- AGENDA: Tasks, appointments, reminders, things to do (e.g., "remind me to call John tomorrow", "meeting at 3pm")
- DIARY: Personal thoughts, reflections, journal entries (e.g., "today was a great day", "I'm feeling...")
- CHAT: Questions, conversations, requests for information or help

User Input: "{user_message}"

If it's AGENDA or DIARY, extract the relevant content and date (if mentioned).
For CHAT messages, provide a helpful, informative, and conversational response. Answer questions thoroughly, give advice when asked, and be engaging.

Return ONLY a valid JSON object:
{{
    "type": "AGENDA" or "DIARY" or "CHAT",
    "content": "extracted content for agenda/diary, or empty for chat",
    "date": "extracted date/time if mentioned, or null",
    "reply": "your helpful response to the user"
}}

Guidelines for replies:
- Be conversational and friendly
- Provide detailed answers to questions
- Give practical advice when asked
- Use markdown formatting for better readability
- Be concise but informative
- Show empathy and understanding
"""
        ai_response_text = generate_content(system_prompt)
        print(f"Raw AI Response: {ai_response_text}")
        try:
            cleaned = ai_response_text.replace('```json', '').replace('```', '').strip()
            ai_data = json.loads(cleaned)
            response_type = ai_data.get('type', 'CHAT').upper()
            content = ai_data.get('content', '')
            reply = ai_data.get('reply', 'I processed that.')
            date = ai_data.get('date')
            if response_type == 'AGENDA':
                add_agenda(content, date, user_id)
            elif response_type == 'DIARY':
                add_diary(content, user_id)
            add_chat('assistant', reply, user_id)
            self.send_json({"reply": reply, "type": response_type})
        except json.JSONDecodeError:
            # Fallback: treat as chat response
            add_chat('assistant', ai_response_text, user_id)
            self.send_json({"reply": ai_response_text, "type": "CHAT"})

    def handle_profile(self, user_id):
        data = self.read_json()
        update_profile(data.get('name'), data.get('photo_path'), user_id)
        self.send_json({"status": "ok"})

    def handle_upload(self, user_id):
        data = self.read_json()
        file_data = data['file_data'].split(',')[1]
        file_bytes = base64.b64decode(file_data)
        filename = f"{uuid.uuid4()}_{data['name']}"
        
        # Save to local uploads directory
        file_path = os.path.join(UPLOADS_DIR, filename)
        with open(file_path, 'wb') as f:
            f.write(file_bytes)
        
        # Return relative path for web access
        file_url = f"/uploads/{filename}"
        
        if 'parent_type' in data and 'parent_id' in data:
            add_attachment(
                data['parent_type'], data['parent_id'],
                file_url, data['name'], data.get('media_type'), user_id
            )
        self.send_json({"path": file_url})

    def handle_attachment(self, user_id):
        data = self.read_json()
        add_attachment(data['parent_type'], data['parent_id'], data['file_path'], data['original_name'], data['media_type'], user_id)
        self.send_json({"status": "ok"})

    # --- PUT helpers ---
    def handle_update_agenda(self, user_id):
        data = self.read_json()
        update_agenda(data['id'], data['content'], data.get('date'), user_id)
        self.send_json({"status": "ok"})

    def handle_update_diary(self, user_id):
        data = self.read_json()
        update_diary(data['id'], data['content'], user_id)
        self.send_json({"status": "ok"})

    # --- DELETE helpers ---
    def handle_delete_agenda(self, user_id):
        data = self.read_json()
        delete_agenda(data['id'], user_id)
        self.send_json({"status": "ok"})

    def handle_delete_diary(self, user_id):
        data = self.read_json()
        delete_diary(data['id'], user_id)
        self.send_json({"status": "ok"})

    def handle_delete_attachment(self, user_id):
        data = self.read_json()
        delete_attachment(data['id'], user_id)
        self.send_json({"status": "ok"})

    def generate_daily_tip(self, user_id):
        """Generate a new daily tip using AI"""
        import random
        categories = ['Productivity', 'Wellness', 'Motivation', 'Learning', 'Mindfulness']
        category = random.choice(categories)
        
        prompt = f"""Generate a single, concise daily tip about {category}. 
        The tip should be:
        - Practical and actionable
        - 1-2 sentences maximum
        - Inspiring and helpful
        - Suitable for a personal assistant app
        
        Return ONLY the tip text, nothing else."""
        
        tip_content = generate_content(prompt).strip()
        add_daily_tip(tip_content, category, user_id)
        
        # Return the newly created tip
        tip = get_daily_tip(user_id)
        self.send_json(tip)

# --- GET helpers ---
def get_agenda_with_attachments(table_type, user_id):
    if table_type == 'agenda':
        items = get_agenda(user_id)
    else:
        items = get_diary(user_id)
    for item in items:
        item['attachments'] = get_attachments(table_type, item['id'], user_id)
    return items

# --- Main ---
if __name__ == "__main__":
    # Initialize users database
    init_users_db()
    
    # Create default user if no users exist and migrate existing data
    default_user_id = create_default_user()
    if default_user_id:
        migrate_existing_data_to_user(default_user_id)
        init_db(default_user_id)
    
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
