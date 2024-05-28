from flask import Flask, render_template, request, redirect
import boto3
import os
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import threading

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# AWS S3 Configuration
S3_BUCKET = 'images-demo1'

s3 = boto3.client('s3')

def multipart_upload(file_path, bucket, key):
    try:
        transfer = boto3.s3.transfer.S3Transfer(s3)
        transfer.upload_file(
            file_path, bucket, key,
            callback=ProgressPercentage(file_path)  # Removed extra_args={'ACL': 'public-read'}
        )
    except (NoCredentialsError, PartialCredentialsError):
        return "Credentials not available"
    except boto3.exceptions.S3UploadFailedError as e:
        return str(e)

class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            print(f"\r{self._filename}  {self._seen_so_far} / {self._size}  ({percentage:.2f}%)", end="")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Upload to S3 using multipart upload
        upload_result = multipart_upload(filepath, S3_BUCKET, filename)
        os.remove(filepath)  # Optional: Remove file after upload

        if upload_result is None:
            return f'File {filename} uploaded successfully to S3!'
        else:
            return f'Failed to upload file: {upload_result}'

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)

