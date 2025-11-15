from flask import Blueprint, request, jsonify, session
import sqlite3
from database import get_db
import bcrypt
import re

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/me')
def get_current_user_me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    db = get_db()
    user = db.execute('''
        SELECT id, username, email, full_name, grade_level, school, created_at, last_login
        FROM users WHERE id = ?
    ''', (user_id,)).fetchone()
    
    if not user:
        session.clear()
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': dict(user)
    })

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def check_password(password, hashed):
    """Check if password matches the hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['username', 'email', 'password', 'full_name']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    username = data['username'].strip()
    email = data['email'].strip().lower()
    password = data['password']
    full_name = data['full_name'].strip()
    grade_level = data.get('grade_level', '').strip()
    school = data.get('school', '').strip()
    
    # Validate email format
    if not is_valid_email(email):
        return jsonify({'success': False, 'error': 'Invalid email format'}), 400
    
    # Validate password strength
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters long'}), 400
    
    db = get_db()
    
    # Check if username or email already exists
    existing_user = db.execute(
        'SELECT id FROM users WHERE username = ? OR email = ?', 
        (username, email)
    ).fetchone()
    
    if existing_user:
        return jsonify({'success': False, 'error': 'Username or email already exists'}), 400
    
    try:
        # Hash password and create user
        password_hash = hash_password(password)
        
        db.execute('''
            INSERT INTO users (username, email, password_hash, full_name, grade_level, school)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, password_hash, full_name, grade_level, school))
        
        db.commit()
        
        # Log the user in automatically
        user = db.execute(
            'SELECT id, username, email, full_name FROM users WHERE username = ?', 
            (username,)
        ).fetchone()
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity (user_id, activity_type, activity_details)
            VALUES (?, ?, ?)
        ''', (user['id'], 'register', 'User registered successfully'))
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': 'Registration failed'}), 500
    finally:
        db.close()

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    data = request.get_json()
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400
    
    db = get_db()
    
    try:
        # Find user by username or email
        user = db.execute('''
            SELECT id, username, email, password_hash, full_name 
            FROM users 
            WHERE (username = ? OR email = ?) AND is_active = 1
        ''', (username, username)).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Check password
        if not check_password(password, user['password_hash']):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Set session
        session['user_id'] = user['id']
        session['username'] = user['username']
        session.permanent = True
        
        # Update last login
        db.execute('''
            UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
        ''', (user['id'],))
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity (user_id, activity_type, activity_details)
            VALUES (?, ?, ?)
        ''', (user['id'], 'login', 'User logged in successfully'))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Login failed'}), 500
    finally:
        db.close()

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """User logout"""
    user_id = session.get('user_id')
    
    if user_id:
        db = get_db()
        try:
            # Log activity
            db.execute('''
                INSERT INTO user_activity (user_id, activity_type, activity_details)
                VALUES (?, ?, ?)
            ''', (user_id, 'logout', 'User logged out'))
            db.commit()
        except:
            pass
        finally:
            db.close()
    
    session.clear()
    return jsonify({'success': True, 'message': 'Logout successful'})

@auth_bp.route('/api/auth/me')
def get_current_user():
    """Get current user information"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    db = get_db()
    user = db.execute('''
        SELECT id, username, email, full_name, grade_level, school, created_at, last_login
        FROM users 
        WHERE id = ?
    ''', (user_id,)).fetchone()
    
    if not user:
        session.clear()
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': dict(user)
    })

def login_required(f):
    """Decorator to require login for routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function