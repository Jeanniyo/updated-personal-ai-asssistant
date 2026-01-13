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
    add_daily_tip, get_daily_tip, get_all_tips
)
from gemini_client import generate_content

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(__file__), 'dist')
UPLOADS_DIR = os.path.join(PUBLIC_DIR, 'uploads')
os.makedirs(UPLOADS_DIR, exist_ok=True)

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
        # API Endpoints
        if self.path == '/api/agenda':
            self.send_json(get_agenda_with_attachments('agenda'))
            return
        if self.path == '/api/diary':
            self.send_json(get_agenda_with_attachments('diary'))
            return
        if self.path == '/api/chat/history':
            self.send_json(get_chats())
            return
        if self.path == '/api/profile':
            self.send_json(get_profile())
            return
        if self.path == '/api/files':
            self.send_json(get_all_attachments())
            return
        if self.path == '/api/daily-tip':
            tip = get_daily_tip()
            if tip:
                self.send_json(tip)
            else:
                # Generate a new tip if none exists for today
                self.generate_daily_tip()
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
        if self.path == '/api/chat':
            self.handle_chat()
            return
        if self.path == '/api/profile':
            self.handle_profile()
            return
        if self.path == '/api/upload':
            self.handle_upload()
            return
        if self.path == '/api/attachment':
            self.handle_attachment()
            return
        if self.path == '/api/daily-tip/generate':
            self.generate_daily_tip()
            return
        self.send_error(404)

    # --- PUT ---
    def do_PUT(self):
        if self.path == '/api/agenda':
            self.handle_update_agenda()
            return
        if self.path == '/api/diary':
            self.handle_update_diary()
            return
        self.send_error(404)

    # --- DELETE ---
    def do_DELETE(self):
        if self.path == '/api/agenda':
            self.handle_delete_agenda()
            return
        if self.path == '/api/diary':
            self.handle_delete_diary()
            return
        if self.path == '/api/files':
            self.handle_delete_attachment()
            return
        self.send_error(404)

    # --- Helpers ---
    def send_json(self, data):
        self.send_response(200)
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
    def handle_chat(self):
        data = self.read_json()
        user_message = data.get('message', '')
        add_chat('user', user_message)

        system_prompt = f"""
        You are a helpful personal assistant. Your job is to categorize the user's input and extract data.
        User Input: "{user_message}"
        Return ONLY a valid JSON object with the structure:
        {{
            "type": "AGENDA" or "DIARY" or "CHAT",
            "content": "...",
            "date": "...",
            "reply": "..."
        }}
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
                add_agenda(content, date)
            elif response_type == 'DIARY':
                add_diary(content)
            add_chat('assistant', reply)
            self.send_json({"reply": reply, "type": response_type})
        except json.JSONDecodeError:
            self.send_json({"reply": ai_response_text, "type": "CHAT"})

    def handle_profile(self):
        data = self.read_json()
        update_profile(data.get('name'), data.get('photo_path'))
        self.send_json({"status": "ok"})

    def handle_upload(self):
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
                file_url, data['name'], data.get('media_type')
            )
        self.send_json({"path": file_url})

    def handle_attachment(self):
        data = self.read_json()
        add_attachment(data['parent_type'], data['parent_id'], data['file_path'], data['original_name'], data['media_type'])
        self.send_json({"status": "ok"})

    # --- PUT helpers ---
    def handle_update_agenda(self):
        data = self.read_json()
        update_agenda(data['id'], data['content'], data.get('date'))
        self.send_json({"status": "ok"})

    def handle_update_diary(self):
        data = self.read_json()
        update_diary(data['id'], data['content'])
        self.send_json({"status": "ok"})

    # --- DELETE helpers ---
    def handle_delete_agenda(self):
        data = self.read_json()
        delete_agenda(data['id'])
        self.send_json({"status": "ok"})

    def handle_delete_diary(self):
        data = self.read_json()
        delete_diary(data['id'])
        self.send_json({"status": "ok"})

    def handle_delete_attachment(self):
        data = self.read_json()
        delete_attachment(data['id'])
        self.send_json({"status": "ok"})

    def generate_daily_tip(self):
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
        add_daily_tip(tip_content, category)
        
        # Return the newly created tip
        tip = get_daily_tip()
        self.send_json(tip)

# --- GET helpers ---
def get_agenda_with_attachments(table_type):
    if table_type == 'agenda':
        items = get_agenda()
    else:
        items = get_diary()
    for item in items:
        item['attachments'] = get_attachments(table_type, item['id'])
    return items

# --- Main ---
if __name__ == "__main__":
    init_db()
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
