from flask import Flask, render_template, request, jsonify, redirect, url_for
from google.cloud import storage
import io
import base64
import os
import subprocess
import tempfile

app = Flask(__name__)

# Initialize Google Cloud Storage client
storage_client = storage.Client()

# Set your Google Cloud Storage bucket name
BUCKET_NAME = "neon-trilogy-429805-g4_cloudbuild"

def upload_blob(bucket_name, source_file, destination_blob_name):
    """Uploads a file to the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_file(source_file)

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)

@app.route("/")
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/process-images', methods=['POST'])
def process_images():
    # Create temporary directories
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, 'data/src')
        targ_path = os.path.join(tmpdir, 'data/targ')
        output_path = os.path.join(tmpdir, 'output')
        os.makedirs(src_path)
        os.makedirs(targ_path)
        os.makedirs(output_path)

        # 1. Save source image
        src_image = request.files['src_image']
        src_filename = os.path.join(src_path, src_image.filename)
        src_image.save(src_filename)
        upload_blob(BUCKET_NAME, open(src_filename, 'rb'), f"DiffFace/data/src/{src_image.filename}")

        # 2. Save target image
        targ_image = request.files['targ_image']
        targ_filename = os.path.join(targ_path, targ_image.filename)
        targ_image.save(targ_filename)
        upload_blob(BUCKET_NAME, open(targ_filename, 'rb'), f"DiffFace/data/targ/{targ_image.filename}")

        # 3. Run the command
        try:
            subprocess.run(['python', 'main.py', '--output_path', output_path], check=True)
        except subprocess.CalledProcessError as e:
            return jsonify({'error': str(e)}), 500

        # 4. Get the first output image
        output_images = [f for f in os.listdir(output_path) if f.endswith(('.png', '.jpg', '.jpeg'))]
        if not output_images:
            return jsonify({'error': 'No output images generated'}), 500

        first_image_path = os.path.join(output_path, output_images[0])
        
        # Upload the output image to Google Cloud Storage
        with open(first_image_path, 'rb') as img_file:
            upload_blob(BUCKET_NAME, img_file, f"DiffFace/output/{output_images[0]}")
        
        # Convert to base64
        with open(first_image_path, 'rb') as img_file:
            img_data = img_file.read()
            img_str = base64.b64encode(img_data).decode('utf-8')
    
    return jsonify({'output_image': img_str})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))