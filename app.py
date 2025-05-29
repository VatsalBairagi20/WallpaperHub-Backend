from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.utils import secure_filename
import os
import uuid

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# MongoDB configuration
client = MongoClient('mongodb+srv://VatsalBairagi:Vatsal2004@vatsal.vgheuph.mongodb.net/')
db = client['final_wallpaper']
wallpapers_collection = db['wallpapers']

# Image upload folder setup (absolute path)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Upload wallpaper endpoint
@app.route('/api/upload-wallpaper', methods=['POST'])
def upload_wallpaper():
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        device = request.form.get('device', '').strip()
        category = request.form.get('category', '').strip()
        new_category = request.form.get('new-category', '').strip()

        if category == 'Create New' and new_category:
            category = new_category

        if not category:
            return jsonify({'error': 'Category name is missing'}), 400

        image = request.files.get('image')
        if not image:
            return jsonify({'error': 'No image uploaded'}), 400

        # Create a unique filename
        filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        print(f"[INFO] Saving image to: {filepath}")

        try:
            image.save(filepath)
        except Exception as e:
            print("[ERROR] Failed to save image:", e)
            return jsonify({'error': 'Failed to save image'}), 500

        # Save metadata in MongoDB
        wallpapers_collection.insert_one({
            'name': name,
            'description': description,
            'category': category,
            'device': device,
            'image_url': f'/uploads/{filename}'
        })

        return jsonify({'message': 'Wallpaper uploaded successfully!'}), 200

    except Exception as e:
        print('[ERROR] Upload failed:', str(e))
        return jsonify({'error': 'Something went wrong'}), 500

# Serve uploaded images
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Get all wallpapers
@app.route('/api/get-wallpapers', methods=['GET'])
def get_wallpapers():
    try:
        wallpapers = list(wallpapers_collection.find())
        for wp in wallpapers:
            wp['_id'] = str(wp['_id'])  # Convert ObjectId to string
        return jsonify({'wallpapers': wallpapers})
    except Exception as e:
        print('[ERROR] Failed to fetch wallpapers:', str(e))
        return jsonify({'error': 'Failed to fetch wallpapers'}), 500

# Get all categories
@app.route('/api/get-categories', methods=['GET'])
def get_categories():
    try:
        categories = wallpapers_collection.distinct('category')
        categories = [cat for cat in categories if cat.strip() != '']
        return jsonify({'categories': categories})
    except Exception as e:
        print('[ERROR] Failed to fetch categories:', str(e))
        return jsonify({'error': 'Failed to fetch categories'}), 500

# Start Flask server
if __name__ == '__main__':
    app.run(debug=True)
