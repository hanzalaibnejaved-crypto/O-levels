from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
import os
import json
import datetime
from datetime import timedelta
from auth import auth_bp, login_required
from routes.subjects import subjects_bp
from routes.resources import resources_bp
from routes.tests import tests_bp
from routes.users import users_bp
from database import init_db, get_db

app = Flask(__name__)
app.secret_key = 'o-levels-platform-secret-key-2024'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize CORS
CORS(app, supports_credentials=True, origins=["http://localhost:8000", "http://192.168.0.35:8000"])

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(subjects_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(tests_bp)
app.register_blueprint(users_bp)

# Initialize database
init_db()

# Sample data for subjects
SUBJECTS_DATA = {
    'mathematics': {
        'id': 1,
        'name': 'Mathematics',
        'code': 'MATH',
        'description': 'Comprehensive mathematics curriculum including algebra, geometry, calculus, and statistics',
        'color': '#ff6b6b',
        'icon': 'calculator',
        'papers': [1, 2],
        'topics': ['Algebra', 'Geometry', 'Trigonometry', 'Calculus', 'Statistics', 'Probability']
    },
    'computer_science': {
        'id': 2,
        'name': 'Computer Science',
        'code': 'COMP',
        'description': 'Computer programming, algorithms, data structures, and computer fundamentals',
        'color': '#4ecdc4',
        'icon': 'laptop-code',
        'papers': [1, 2],
        'topics': ['Programming', 'Algorithms', 'Data Structures', 'Databases', 'Computer Architecture']
    },
    'chemistry': {
        'id': 3,
        'name': 'Chemistry',
        'code': 'CHEM',
        'description': 'Study of elements, compounds, chemical reactions, and molecular structures',
        'color': '#45b7d1',
        'icon': 'flask',
        'papers': [1, 2, 3],
        'topics': ['Organic Chemistry', 'Inorganic Chemistry', 'Physical Chemistry', 'Analytical Chemistry']
    },
    'physics': {
        'id': 4,
        'name': 'Physics',
        'code': 'PHYS',
        'description': 'Fundamental principles of matter, energy, motion, and the laws of the universe',
        'color': '#ffa726',
        'icon': 'atom',
        'papers': [1, 2, 3],
        'topics': ['Mechanics', 'Electricity', 'Magnetism', 'Thermodynamics', 'Waves', 'Modern Physics']
    },
    'english': {
        'id': 5,
        'name': 'English',
        'code': 'ENG',
        'description': 'Language skills, literature analysis, and communication techniques',
        'color': '#ba68c8',
        'icon': 'book-open',
        'papers': [1, 2],
        'topics': ['Grammar', 'Comprehension', 'Composition', 'Literature', 'Vocabulary']
    },
    'islamiat': {
        'id': 6,
        'name': 'Islamiat',
        'code': 'ISL',
        'description': 'Islamic studies including history, beliefs, practices, and moral teachings',
        'color': '#66bb6a',
        'icon': 'mosque',
        'papers': [1, 2],
        'topics': ['Quran', 'Hadith', 'Islamic History', 'Fiqh', 'Islamic Ethics']
    },
    'pakistan_studies': {
        'id': 7,
        'name': 'Pakistan Studies',
        'code': 'PST',
        'description': 'History, culture, geography, and political development of Pakistan',
        'color': '#78909c',
        'icon': 'globe-asia',
        'papers': [1, 2],
        'topics': ['Pakistan Movement', 'Geography', 'Culture', 'Economy', 'Political System']
    }
}



@app.route('/')
def index():
    """Serve the main application"""
    return render_template('index.html')

@app.route('/api/subjects')
def get_subjects():
    """Get all available subjects"""
    return jsonify({
        'success': True,
        'subjects': SUBJECTS_DATA
    })

@app.route('/api/subjects/<subject_name>')
def get_subject_detail(subject_name):
    """Get detailed information about a specific subject"""
    subject = SUBJECTS_DATA.get(subject_name)
    if not subject:
        return jsonify({'success': False, 'error': 'Subject not found'}), 404
    
    # Get resources for this subject
    db = get_db()
    resources = db.execute('''
        SELECT * FROM resources WHERE subject_id = ? ORDER BY created_at DESC
    ''', (subject['id'],)).fetchall()
    
    subject_resources = []
    for resource in resources:
        subject_resources.append(dict(resource))
    
    return jsonify({
        'success': True,
        'subject': subject,
        'resources': subject_resources
    })

@app.route('/api/dashboard/stats')
@login_required
def dashboard_stats():
    """Get dashboard statistics for logged in user"""
    user_id = session.get('user_id')
    db = get_db()
    
    # Get user progress
    progress = db.execute('''
        SELECT subject_id, COUNT(*) as completed_count 
        FROM user_progress 
        WHERE user_id = ? AND completed = 1 
        GROUP BY subject_id
    ''', (user_id,)).fetchall()
    
    # Get recent activity
    activity = db.execute('''
        SELECT * FROM user_activity 
        WHERE user_id = ? 
        ORDER BY activity_date DESC 
        LIMIT 10
    ''', (user_id,)).fetchall()
    
    return jsonify({
        'success': True,
        'progress': [dict(p) for p in progress],
        'recent_activity': [dict(a) for a in activity]
    })

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Handle file uploads for resources"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Validate file type
    allowed_extensions = {'pdf', 'doc', 'docx', 'ppt', 'pptx', 'jpg', 'jpeg', 'png', 'mp4', 'avi', 'mov'}
    if '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400
    
    # Save file
    filename = f"{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)
    
    return jsonify({
        'success': True,
        'filename': filename,
        'message': 'File uploaded successfully'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True, host='0.0.0.0', port=5000)