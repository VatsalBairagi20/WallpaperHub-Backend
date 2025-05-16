from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# MongoDB config
client = MongoClient('mongodb+srv://VatsalBairagi:Vatsal2004@vatsal.vgheuph.mongodb.net/')
db = client['final_wallpaper']
wallpapers_collection = db['wallpapers']

# Folder to store uploaded images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

        filename = secure_filename(image.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        image.save(filepath)

        wallpapers_collection.insert_one({
            'name': name,
            'description': description,
            'category': category,
            'device': device,
            'image_url': f'/uploads/{filename}'
        })

        return jsonify({'message': 'Wallpaper uploaded successfully!'}), 200
    except Exception as e:
        print('UPLOAD ERROR:', str(e))
        return jsonify({'error': 'Something went wrong'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/api/get-wallpapers', methods=['GET'])
def get_wallpapers():
    try:
        wallpapers = list(wallpapers_collection.find())
        for wp in wallpapers:
            wp['_id'] = str(wp['_id'])  # Convert ObjectId to string
        return jsonify({'wallpapers': wallpapers})
    except Exception as e:
        print('GET WALLPAPERS ERROR:', str(e))
        return jsonify({'error': 'Failed to fetch wallpapers'}), 500

@app.route('/api/get-categories', methods=['GET'])
def get_categories():
    try:
        categories = wallpapers_collection.distinct('category')
        categories = [cat for cat in categories if cat.strip() != '']
        return jsonify({'categories': categories})
    except Exception as e:
        print('GET CATEGORIES ERROR:', str(e))
        return jsonify({'error': 'Failed to fetch categories'}), 500

if __name__ == '__main__':
    app.run(debug=True)
