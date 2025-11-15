from flask import Blueprint, request, jsonify
from database import get_db

subjects_bp = Blueprint('subjects', __name__)

@subjects_bp.route('/api/subjects', methods=['GET'])
def get_all_subjects():
    """Get all subjects with statistics"""
    db = get_db()
    
    try:
        subjects = db.execute('''
            SELECT s.*, 
                   COUNT(DISTINCT r.id) as resource_count,
                   COUNT(DISTINCT CASE WHEN r.resource_type = 'notes' THEN r.id END) as notes_count,
                   COUNT(DISTINCT CASE WHEN r.resource_type = 'video' THEN r.id END) as videos_count,
                   COUNT(DISTINCT CASE WHEN r.resource_type = 'questions' THEN r.id END) as questions_count,
                   COUNT(DISTINCT CASE WHEN r.resource_type = 'past_paper' THEN r.id END) as past_papers_count
            FROM subjects s
            LEFT JOIN resources r ON s.id = r.subject_id
            GROUP BY s.id
            ORDER BY s.name
        ''').fetchall()
        
        subjects_list = []
        for subject in subjects:
            subject_dict = dict(subject)
            subjects_list.append(subject_dict)
        
        return jsonify({
            'success': True,
            'subjects': subjects_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@subjects_bp.route('/api/subjects/<int:subject_id>', methods=['GET'])
def get_subject_by_id(subject_id):
    """Get detailed information about a specific subject"""
    db = get_db()
    
    try:
        subject = db.execute('''
            SELECT s.*, 
                   COUNT(DISTINCT r.id) as total_resources
            FROM subjects s
            LEFT JOIN resources r ON s.id = r.subject_id
            WHERE s.id = ?
            GROUP BY s.id
        ''', (subject_id,)).fetchone()
        
        if not subject:
            return jsonify({'success': False, 'error': 'Subject not found'}), 404
        
        # Get resources by type
        resources_by_type = {}
        resource_types = ['notes', 'video', 'questions', 'past_paper']
        
        for resource_type in resource_types:
            resources = db.execute('''
                SELECT r.*, u.username as uploaded_by_username
                FROM resources r
                LEFT JOIN users u ON r.uploaded_by = u.id
                WHERE r.subject_id = ? AND r.resource_type = ?
                ORDER BY r.created_at DESC
            ''', (subject_id, resource_type)).fetchall()
            
            resources_by_type[resource_type] = [dict(resource) for resource in resources]
        
        # Get topics for this subject
        topics = db.execute('''
            SELECT DISTINCT topic 
            FROM resources 
            WHERE subject_id = ? AND topic IS NOT NULL 
            ORDER BY topic
        ''', (subject_id,)).fetchall()
        
        topics_list = [topic['topic'] for topic in topics]
        
        return jsonify({
            'success': True,
            'subject': dict(subject),
            'resources': resources_by_type,
            'topics': topics_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@subjects_bp.route('/api/subjects/<int:subject_id>/progress', methods=['GET'])
def get_subject_progress(subject_id):
    """Get user progress for a specific subject"""
    from auth import login_required
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'success': False, 'error': 'User ID required'}), 400
    
    db = get_db()
    
    try:
        # Get overall progress
        progress = db.execute('''
            SELECT 
                COUNT(*) as total_resources,
                COUNT(CASE WHEN up.completed = 1 THEN 1 END) as completed_resources,
                AVG(CASE WHEN up.score IS NOT NULL THEN up.score END) as average_score,
                SUM(up.time_spent) as total_time_spent
            FROM resources r
            LEFT JOIN user_progress up ON r.id = up.resource_id AND up.user_id = ?
            WHERE r.subject_id = ?
        ''', (user_id, subject_id)).fetchone()
        
        # Get progress by resource type
        progress_by_type = db.execute('''
            SELECT 
                r.resource_type,
                COUNT(*) as total,
                COUNT(CASE WHEN up.completed = 1 THEN 1 END) as completed,
                ROUND(COUNT(CASE WHEN up.completed = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as completion_rate
            FROM resources r
            LEFT JOIN user_progress up ON r.id = up.resource_id AND up.user_id = ?
            WHERE r.subject_id = ?
            GROUP BY r.resource_type
        ''', (user_id, subject_id)).fetchall()
        
        return jsonify({
            'success': True,
            'progress': dict(progress),
            'progress_by_type': [dict(p) for p in progress_by_type]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()