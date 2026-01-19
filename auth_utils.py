import os
import json
import jwt
import bcrypt
from datetime import datetime, timedelta

# Secret key for JWT - in production, this should be in environment variables
SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
USERS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'users.json')

def init_users_db():
    """Initialize users database file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump([], f, indent=2)

def _read_users():
    """Read users from JSON file"""
    init_users_db()
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def _write_users(users):
    """Write users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_user_by_username(username):
    """Get user by username"""
    users = _read_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def get_user_by_id(user_id):
    """Get user by ID"""
    users = _read_users()
    for user in users:
        if user['id'] == user_id:
            return user
    return None

def register_user(username, password):
    """
    Register a new user
    Returns: (success: bool, message: str, user_id: str or None)
    """
    if not username or not password:
        return False, "Username and password are required", None
    
    if len(password) < 6:
        return False, "Password must be at least 6 characters", None
    
    # Check if user already exists
    if get_user_by_username(username):
        return False, "Username already exists", None
    
    users = _read_users()
    
    # Generate user ID
    user_id = str(len(users) + 1)
    
    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Create user object
    new_user = {
        'id': user_id,
        'username': username,
        'password_hash': password_hash,
        'created_at': datetime.now().isoformat()
    }
    
    users.append(new_user)
    _write_users(users)
    
    # Create user data directory
    user_data_dir = os.path.join(os.path.dirname(__file__), 'data', user_id)
    os.makedirs(user_data_dir, exist_ok=True)
    
    return True, "User registered successfully", user_id

def login_user(username, password):
    """
    Authenticate user and generate JWT token
    Returns: (success: bool, message: str, token: str or None, user_data: dict or None)
    """
    if not username or not password:
        return False, "Username and password are required", None, None
    
    user = get_user_by_username(username)
    if not user:
        return False, "Invalid username or password", None, None
    
    # Verify password
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return False, "Invalid username or password", None, None
    
    # Generate JWT token (expires in 7 days)
    payload = {
        'user_id': user['id'],
        'username': user['username'],
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    
    user_data = {
        'id': user['id'],
        'username': user['username'],
        'created_at': user['created_at']
    }
    
    return True, "Login successful", token, user_data

def verify_token(token):
    """
    Verify JWT token and return user data
    Returns: (success: bool, user_data: dict or None)
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user = get_user_by_id(payload['user_id'])
        if user:
            return True, {
                'id': user['id'],
                'username': user['username']
            }
        return False, None
    except jwt.ExpiredSignatureError:
        return False, None
    except jwt.InvalidTokenError:
        return False, None

def create_default_user():
    """
    Create a default admin user if no users exist
    This is used for migrating existing data
    """
    users = _read_users()
    if len(users) == 0:
        # Create default admin user
        success, message, user_id = register_user('admin', 'admin123')
        if success:
            print(f"Created default user: admin (password: admin123)")
            print(f"User ID: {user_id}")
            return user_id
    return None
