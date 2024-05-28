import os
import io
from flask import Flask, request, redirect, url_for, render_template, session
from werkzeug.utils import secure_filename
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import google.auth.transport.requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load the service account credentials
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = 'path_to_service_account.json'
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        upload_to_drive(file_path, filename)
        return 'File successfully uploaded to Google Drive'
    else:
        return 'Allowed file types are png, jpg, jpeg, gif'

def upload_to_drive(file_path, filename):
    file_metadata = {'name': filename}
    media = MediaFileUpload(file_path, mimetype='image/jpeg')
    drive_service.files().create(body=file_metadata, media_body=media, fields='id').execute()

if __name__ == "__main__":
    app.run(debug=True)

