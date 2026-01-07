
import urllib.request
import json
import os

# Manual .env parser for zero-dependency environment
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

# You should start the server with GEMINI_API_KEY environment variable set or in .env file
API_KEY = os.environ.get("GEMINI_API_KEY")

def generate_content(prompt):
    if not API_KEY:
        return "Error: GEMINI_API_KEY not found in environment."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{"text": prompt}]
        }]
    }
    
    encoded_data = json.dumps(data).encode("utf-8")
    
    try:
        req = urllib.request.Request(url, data=encoded_data, headers=headers)
        with urllib.request.urlopen(req) as response:
            response_body = response.read().decode("utf-8")
            result = json.loads(response_body)
            # Extract text from response structure
            try:
                msg = result['candidates'][0]['content']['parts'][0]['text']
                return msg
            except (KeyError, IndexError):
                return "Error parsing Gemini response."
                
    except urllib.error.HTTPError as e:
        return f"HTTP Error: {e.code} - {e.reason}"
    except Exception as e:
        return f"Error: {str(e)}"
