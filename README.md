# AI Personal Assistant

A personal AI assistant with agenda, diary, chat, and file management features.

## Features
- 💬 AI-powered chat interface
- 📅 Agenda management
- 📔 Diary entries
- 📁 File attachments
- 💡 Daily tips
- 👤 User profile

## Tech Stack
- **Backend**: Python 3.11+ (no database required - uses JSON storage)
- **Frontend**: React + Vite
- **AI**: Google Gemini API

## Deployment

### Railway (Free Tier Compatible)
This app uses **JSON file storage** - no database required!

1. Push your code to GitHub
2. Connect your GitHub repo to Railway
3. Add environment variable: `GEMINI_API_KEY`
4. Deploy! 🚀

### Other Platforms
- **Fly.io**: `fly launch` (free tier available)
- **PythonAnywhere**: Upload and configure
- **Vercel**: Deploy frontend + serverless backend

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
npm install
```

2. Build frontend:
```bash
npm run build
```

3. Set environment variables:
```bash
export GEMINI_API_KEY=your_api_key_here
```

4. Run server:
```bash
python server.py
```

5. Open http://localhost:8000

## Environment Variables
- `GEMINI_API_KEY` - Your Google Gemini API key (required)
- `PORT` - Server port (default: 8000)

## Storage
All data is stored in JSON files in the `data/` directory:
- `agenda.json` - Agenda items
- `diary.json` - Diary entries
- `chat_history.json` - Chat messages
- `profile.json` - User profile
- `daily_tips.json` - Daily tips
- `attachments.json` - File metadata

## License
MIT
