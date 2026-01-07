import os
import json
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload, MediaIoBaseUpload
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveClient:
    def __init__(self):
        self.creds = None
        self.service = None
        self.data_folder_id = None
        self.uploads_folder_id = None
        self.authenticate()
        self.setup_folders()
    
    def authenticate(self):
        """Authenticate with Google Drive API"""
        # The file token.json stores the user's access and refresh tokens
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # If there are no (valid) credentials available, let the user log in
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())
        
        self.service = build('drive', 'v3', credentials=self.creds)
    
    def setup_folders(self):
        """Create or find the PersonalAssistantData folder and uploads subfolder"""
        try:
            # Search for PersonalAssistantData folder
            query = "name='PersonalAssistantData' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if items:
                self.data_folder_id = items[0]['id']
            else:
                # Create the folder
                file_metadata = {
                    'name': 'PersonalAssistantData',
                    'mimeType': 'application/vnd.google-apps.folder'
                }
                folder = self.service.files().create(body=file_metadata, fields='id').execute()
                self.data_folder_id = folder.get('id')
            
            # Setup uploads subfolder
            query = f"name='uploads' and '{self.data_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if items:
                self.uploads_folder_id = items[0]['id']
            else:
                file_metadata = {
                    'name': 'uploads',
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.data_folder_id]
                }
                folder = self.service.files().create(body=file_metadata, fields='id').execute()
                self.uploads_folder_id = folder.get('id')
                
        except HttpError as error:
            error_content = str(error)
            if "accessNotConfigured" in error_content or "Google Drive API has not been used" in error_content:
                print("\n\033[91m" + "="*80)
                print("CRITICAL ERROR: Google Drive API is not enabled.")
                print("To fix this, please visit the following URL to enable the API for your project:")
                
                # Extract URL from error message if possible
                import re
                url_match = re.search(r'https://console\.developers\.google\.com/apis/api/drive\.googleapis\.com/overview\?project=\d+', error_content)
                if url_match:
                    print(f"\n{url_match.group(0)}\n")
                else:
                    print("\nhttps://console.developers.google.com/apis/api/drive.googleapis.com\n")
                
                print("After enabling the API, wait a few minutes and run the server again.")
                print("="*80 + "\033[0m\n")
                import sys
                sys.exit(1)
            
            print(f'An error occurred: {error}')
            raise
    
    def read_json_file(self, file_name):
        """Read a JSON file from Google Drive"""
        try:
            query = f"name='{file_name}' and '{self.data_folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            if not items:
                return None
            
            file_id = items[0]['id']
            request = self.service.files().get_media(fileId=file_id)
            file_content = io.BytesIO()
            downloader = MediaIoBaseDownload(file_content, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_content.seek(0)
            return json.loads(file_content.read().decode('utf-8'))
            
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def write_json_file(self, file_name, data):
        """Write a JSON file to Google Drive"""
        try:
            json_data = json.dumps(data, indent=2)
            file_content = io.BytesIO(json_data.encode('utf-8'))
            
            # Check if file exists
            query = f"name='{file_name}' and '{self.data_folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
            items = results.get('files', [])
            
            media = MediaIoBaseUpload(file_content, mimetype='application/json', resumable=True)
            
            if items:
                # Update existing file
                file_id = items[0]['id']
                self.service.files().update(fileId=file_id, media_body=media).execute()
            else:
                # Create new file
                file_metadata = {
                    'name': file_name,
                    'parents': [self.data_folder_id]
                }
                self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def upload_file(self, file_path, original_name):
        """Upload a file to the uploads folder"""
        try:
            file_metadata = {
                'name': original_name,
                'parents': [self.uploads_folder_id]
            }
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            return file.get('id')
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise
    
    def get_file_url(self, file_id):
        """Get a shareable URL for a file"""
        try:
            # Make file accessible to anyone with the link
            permission = {
                'type': 'anyone',
                'role': 'reader'
            }
            self.service.permissions().create(fileId=file_id, body=permission).execute()
            
            # Get the file metadata
            file = self.service.files().get(fileId=file_id, fields='webViewLink, webContentLink').execute()
            return file.get('webContentLink', file.get('webViewLink'))
        except HttpError as error:
            print(f'An error occurred: {error}')
            return None
    
    def delete_file(self, file_id):
        """Delete a file from Google Drive"""
        try:
            self.service.files().delete(fileId=file_id).execute()
        except HttpError as error:
            print(f'An error occurred: {error}')
            raise

# Singleton instance
_drive_client = None

def get_drive_client():
    """Get or create the Google Drive client instance"""
    global _drive_client
    if _drive_client is None:
        _drive_client = GoogleDriveClient()
    return _drive_client
