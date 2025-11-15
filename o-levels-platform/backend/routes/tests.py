from flask import Blueprint, request, jsonify
import json
from database import get_db
from auth import login_required

tests_bp = Blueprint('tests', __name__)

@tests_bp.route('/api/tests/generate', methods=['POST'])
@login_required
def generate_test():
    """Generate a custom test based on criteria"""
    from flask import session
    data = request.get_json()
    
    required_fields = ['subject_id', 'title']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'error': f'{field} is required'}), 400
    
    db = get_db()
    
    try:
        # Get questions based on criteria
        query = '''
            SELECT * FROM questions 
            WHERE subject_id = ? AND difficulty = ?
        '''
        params = [data['subject_id'], data.get('difficulty', 'medium')]
        
        if data.get('topics'):
            topics = data['topics']
            placeholders = ','.join(['?'] * len(topics))
            query += f' AND topic IN ({placeholders})'
            params.extend(topics)
        
        if data.get('question_types'):
            question_types = data['question_types']
            placeholders = ','.join(['?'] * len(question_types))
            query += f' AND question_type IN ({placeholders})'
            params.extend(question_types)
        
        questions = db.execute(query, params).fetchall()
        
        # Limit questions based on marks
        total_marks = data.get('total_marks', 100)
        selected_questions = []
        current_marks = 0
        
        for question in questions:
            if current_marks + question['marks'] <= total_marks:
                selected_questions.append(dict(question))
                current_marks += question['marks']
            
            if current_marks >= total_marks:
                break
        
        # Create test record
        test_id = db.execute('''
            INSERT INTO tests (
                user_id, title, subject_id, paper_number, difficulty, 
                total_marks, time_limit, question_types, custom_questions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session.get('user_id'),
            data['title'],
            data['subject_id'],
            data.get('paper_number'),
            data.get('difficulty', 'medium'),
            total_marks,
            data.get('time_limit', 180),
            json.dumps(data.get('question_types', [])),
            json.dumps([q['id'] for q in selected_questions])
        )).lastrowid
        
        db.commit()
        
        return jsonify({
            'success': True,
            'test_id': test_id,
            'questions': selected_questions,
            'total_questions': len(selected_questions),
            'total_marks': current_marks
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@tests_bp.route('/api/tests/<int:test_id>', methods=['GET'])
def get_test(test_id):
    """Get test details and questions"""
    db = get_db()
    
    try:
        test = db.execute('''
            SELECT t.*, s.name as subject_name, u.username as creator_username
            FROM tests t
            JOIN subjects s ON t.subject_id = s.id
            JOIN users u ON t.user_id = u.id
            WHERE t.id = ?
        ''', (test_id,)).fetchone()
        
        if not test:
            return jsonify({'success': False, 'error': 'Test not found'}), 404
        
        # Get questions for this test
        custom_questions = json.loads(test['custom_questions'] or '[]')
        questions = []
        
        if custom_questions:
            placeholders = ','.join(['?'] * len(custom_questions))
            questions = db.execute(f'''
                SELECT * FROM questions WHERE id IN ({placeholders})
            ''', custom_questions).fetchall()
        
        return jsonify({
            'success': True,
            'test': dict(test),
            'questions': [dict(q) for q in questions]
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@tests_bp.route('/api/tests/<int:test_id>/submit', methods=['POST'])
@login_required
def submit_test(test_id):
    """Submit test answers and calculate score"""
    from flask import session
    data = request.get_json()
    
    answers = data.get('answers', {})
    
    db = get_db()
    
    try:
        # Get test and questions
        test = db.execute('SELECT * FROM tests WHERE id = ?', (test_id,)).fetchone()
        if not test:
            return jsonify({'success': False, 'error': 'Test not found'}), 404
        
        custom_questions = json.loads(test['custom_questions'] or '[]')
        questions = db.execute(f'''
            SELECT * FROM questions WHERE id IN ({','.join(['?'] * len(custom_questions))})
        ''', custom_questions).fetchall()
        
        # Calculate score
        total_score = 0
        max_score = 0
        results = {}
        
        for question in questions:
            max_score += question['marks']
            user_answer = answers.get(str(question['id']))
            
            if user_answer and user_answer == question['correct_answer']:
                total_score += question['marks']
                results[str(question['id'])] = {
                    'correct': True,
                    'score': question['marks'],
                    'user_answer': user_answer,
                    'correct_answer': question['correct_answer']
                }
            else:
                results[str(question['id'])] = {
                    'correct': False,
                    'score': 0,
                    'user_answer': user_answer,
                    'correct_answer': question['correct_answer']
                }
        
        percentage = (total_score / max_score) * 100 if max_score > 0 else 0
        
        # Update test record
        db.execute('''
            UPDATE tests 
            SET is_completed = 1, score = ?, time_taken = ?
            WHERE id = ?
        ''', (percentage, data.get('time_taken'), test_id))
        
        db.commit()
        
        return jsonify({
            'success': True,
            'score': total_score,
            'max_score': max_score,
            'percentage': percentage,
            'results': results
        })
        
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()