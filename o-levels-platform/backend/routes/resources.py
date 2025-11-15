from flask import Blueprint, request, jsonify, send_file
import os
from database import get_db
from auth import login_required

resources_bp = Blueprint('resources', __name__)

@resources_bp.route('/api/resources', methods=['GET'])
def get_resources():
    """Get resources with filtering and pagination"""
    subject_id = request.args.get('subject_id')
    resource_type = request.args.get('type')
    topic = request.args.get('topic')
    difficulty = request.args.get('difficulty')
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    
    db = get_db()
    
    try:
        # Build query
        query = '''
            SELECT r.*, s.name as subject_name, s.code as subject_code, u.username as uploaded_by_username
            FROM resources r
            JOIN subjects s ON r.subject_id = s.id
            LEFT JOIN users u ON r.uploaded_by = u.id
            WHERE 1=1
        '''
        params = []
        
        if subject_id:
            query += ' AND r.subject_id = ?'
            params.append(subject_id)
        
        if resource_type:
            query += ' AND r.resource_type = ?'
            params.append(resource_type)
        
        if topic:
            query += ' AND r.topic = ?'
            params.append(topic)
        
        if difficulty:
            query += ' AND r.difficulty = ?'
            params.append(difficulty)
        
        # Count total
        count_query = 'SELECT COUNT(*) as total FROM resources r WHERE 1=1'
        count_params = params.copy()
        
        if subject_id:
            count_query += ' AND r.subject_id = ?'
        if resource_type:
            count_query += ' AND r.resource_type = ?'
        if topic:
            count_query += ' AND r.topic = ?'
        if difficulty:
            count_query += ' AND r.difficulty = ?'
        
        total = db.execute(count_query, count_params).fetchone()['total']
        
        # Add pagination
        query += ' ORDER BY r.created_at DESC LIMIT ? OFFSET ?'
        params.extend([per_page, (page - 1) * per_page])
        
        resources = db.execute(query, params).fetchall()
        
        return jsonify({
            'success': True,
            'resources': [dict(resource) for resource in resources],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@resources_bp.route('/api/resources/<int:resource_id>', methods=['GET'])
def get_resource(resource_id):
    """Get specific resource details"""
    db = get_db()
    
    try:
        resource = db.execute('''
            SELECT r.*, s.name as subject_name, s.code as subject_code, u.username as uploaded_by_username
            FROM resources r
            JOIN subjects s ON r.subject_id = s.id
            LEFT JOIN users u ON r.uploaded_by = u.id
            WHERE r.id = ?
        ''', (resource_id,)).fetchone()
        
        if not resource:
            return jsonify({'success': False, 'error': 'Resource not found'}), 404
        
        # Increment view count
        db.execute('UPDATE resources SET view_count = view_count + 1 WHERE id = ?', (resource_id,))
        db.commit()
        
        return jsonify({
            'success': True,
            'resource': dict(resource)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@resources_bp.route('/api/resources/<int:resource_id>/download', methods=['GET'])
def download_resource(resource_id):
    """Download resource file"""
    db = get_db()
    
    try:
        resource = db.execute('SELECT * FROM resources WHERE id = ?', (resource_id,)).fetchone()
        
        if not resource or not resource['file_path']:
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        file_path = resource['file_path']
        
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found on server'}), 404
        
        # Increment download count
        db.execute('UPDATE resources SET download_count = download_count + 1 WHERE id = ?', (resource_id,))
        db.commit()
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@resources_bp.route('/api/resources', methods=['POST'])
@login_required
def create_resource():
    """Create a new resource (admin/teacher only)"""
    from flask import session
    data = request.get_json()
    
    required_fields = ['subject_id', 'title', 'resource_type']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    db = get_db()
    
    try:
        db.execute('''
            INSERT INTO resources (
                subject_id, title, description, resource_type, file_path, file_size,
                duration, difficulty, marks, paper_number, year, topic, uploaded_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['subject_id'],
            data['title'],
            data.get('description'),
            data['resource_type'],
            data.get('file_path'),
            data.get('file_size'),
            data.get('duration'),
            data.get('difficulty'),
            data.get('marks'),
            data.get('paper_number'),
            data.get('year'),
            data.get('topic'),
            session.get('user_id')
        ))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'message': 'Resource created successfully'
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()