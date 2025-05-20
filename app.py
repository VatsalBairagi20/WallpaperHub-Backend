from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from pymongo import MongoClient
import os
import requests
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

# Pixabay API key
PIXABAY_API_KEY = '47849701-73acc40f5327790e47c2f6a81'


# 🔥 AUTO FETCH ON SERVER STARTUP
def fetch_wallpapers_on_startup():
    try:
        query = 'nature'  # Change this to any category you want
        device = 'PC'
        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo&per_page=10"
        res = requests.get(url)
        wallpapers = res.json().get('hits', [])

        if not wallpapers:
            print('❌ No wallpapers found during startup fetch.')
            return

        added = 0
        for wp in wallpapers:
            image_url = wp.get('largeImageURL')
            name = wp.get('tags', 'Wallpaper')

            # Avoid duplicates
            exists = wallpapers_collection.find_one({'image_url': image_url})
            if exists:
                continue

            wallpapers_collection.insert_one({
                'name': name,
                'description': f'Auto-fetched for {query}',
                'category': query,
                'device': device,
                'image_url': image_url
            })
            added += 1

        print(f'✅ {added} wallpapers auto-added to category "{query}".')

    except Exception as e:
        print('🚨 Startup fetch error:', str(e))


# Upload endpoint
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


# Serve uploaded files
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# Get all wallpapers
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


# Get all categories
@app.route('/api/get-categories', methods=['GET'])
def get_categories():
    try:
        categories = wallpapers_collection.distinct('category')
        categories = [cat for cat in categories if cat.strip() != '']
        return jsonify({'categories': categories})
    except Exception as e:
        print('GET CATEGORIES ERROR:', str(e))
        return jsonify({'error': 'Failed to fetch categories'}), 500


# 🗑️ OPTIONAL: Keep this if you still want to manually fetch (not used by frontend anymore)
@app.route('/api/fetch-wallpapers', methods=['POST'])
def fetch_wallpapers():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        device = data.get('device', 'PC')

        if not query:
            return jsonify({'error': 'Query/category is missing'}), 400

        url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo&per_page=10"
        res = requests.get(url)
        wallpapers = res.json().get('hits', [])

        if not wallpapers:
            return jsonify({'error': 'No wallpapers found'}), 404

        added = 0
        for wp in wallpapers:
            image_url = wp.get('largeImageURL')
            name = wp.get('tags', 'Wallpaper')

            # Avoid duplicates
            exists = wallpapers_collection.find_one({'image_url': image_url})
            if exists:
                continue

            wallpapers_collection.insert_one({
                'name': name,
                'description': f'Auto-fetched for {query}',
                'category': query,
                'device': device,
                'image_url': image_url
            })
            added += 1

        return jsonify({'message': f'{added} wallpapers added to category "{query}"'}), 200

    except Exception as e:
        print('FETCH ERROR:', str(e))
        return jsonify({'error': 'Failed to fetch wallpapers'}), 500


# 🔃 RUN SERVER + AUTO FETCH
if __name__ == '__main__':
    fetch_wallpapers_on_startup()
    app.run(debug=True)
