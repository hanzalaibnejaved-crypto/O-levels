from flask import Blueprint, request, jsonify
from database import get_db
from auth import login_required

users_bp = Blueprint('users', __name__)

@users_bp.route('/api/users/<int:user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    """Get user profile information"""
    db = get_db()
    
    try:
        user = db.execute('''
            SELECT id, username, email, full_name, grade_level, school, created_at, last_login
            FROM users 
            WHERE id = ? AND is_active = 1
        ''', (user_id,)).fetchone()
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': dict(user)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@users_bp.route('/api/users/<int:user_id>/progress', methods=['GET'])
def get_user_progress(user_id):
    """Get user progress across all subjects"""
    db = get_db()
    
    try:
        # Overall progress
        overall = db.execute('''
            SELECT 
                COUNT(DISTINCT r.id) as total_resources,
                COUNT(DISTINCT CASE WHEN up.completed = 1 THEN up.resource_id END) as completed_resources,
                SUM(up.time_spent) as total_time_spent,
                AVG(up.score) as average_score
            FROM resources r
            LEFT JOIN user_progress up ON r.id = up.resource_id AND up.user_id = ?
        ''', (user_id,)).fetchone()
        
        # Progress by subject
        by_subject = db.execute('''
            SELECT 
                s.id, s.name, s.code, s.color, s.icon,
                COUNT(DISTINCT r.id) as total_resources,
                COUNT(DISTINCT CASE WHEN up.completed = 1 THEN up.resource_id END) as completed_resources,
                ROUND(COUNT(DISTINCT CASE WHEN up.completed = 1 THEN up.resource_id END) * 100.0 / COUNT(DISTINCT r.id), 2) as completion_rate,
                AVG(up.score) as average_score,
                SUM(up.time_spent) as time_spent
            FROM subjects s
            LEFT JOIN resources r ON s.id = r.subject_id
            LEFT JOIN user_progress up ON r.id = up.resource_id AND up.user_id = ?
            GROUP BY s.id
            ORDER BY completion_rate DESC
        ''', (user_id,)).fetchall()
        
        # Recent activity
        activity = db.execute('''
            SELECT activity_type, activity_details, activity_date
            FROM user_activity 
            WHERE user_id = ? 
            ORDER BY activity_date DESC 
            LIMIT 10
        ''', (user_id,)).fetchall()
        
        return jsonify({
            'success': True,
            'overall': dict(overall),
            'by_subject': [dict(subject) for subject in by_subject],
            'recent_activity': [dict(activity) for activity in activity]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@users_bp.route('/api/users/<int:user_id>/update-progress', methods=['POST'])
@login_required
def update_user_progress(user_id):
    """Update user progress for a resource"""
    from flask import session
    data = request.get_json()
    
    required_fields = ['resource_id', 'progress_type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    db = get_db()
    
    try:
        # Check if progress record exists
        existing = db.execute('''
            SELECT id FROM user_progress 
            WHERE user_id = ? AND resource_id = ?
        ''', (user_id, data['resource_id'])).fetchone()
        
        if existing:
            # Update existing record
            db.execute('''
                UPDATE user_progress 
                SET progress_type = ?, completed = ?, score = ?, time_spent = ?, notes = ?, last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (
                data['progress_type'],
                data.get('completed', 0),
                data.get('score'),
                data.get('time_spent'),
                data.get('notes'),
                existing['id']
            ))
        else:
            # Create new record
            db.execute('''
                INSERT INTO user_progress (user_id, resource_id, progress_type, completed, score, time_spent, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data['resource_id'],
                data['progress_type'],
                data.get('completed', 0),
                data.get('score'),
                data.get('time_spent'),
                data.get('notes')
            ))
        
        # Log activity
        db.execute('''
            INSERT INTO user_activity (user_id, activity_type, activity_details)
            VALUES (?, ?, ?)
        ''', (user_id, 'progress_update', f'Updated progress for resource {data["resource_id"]}'))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Progress updated successfully'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()