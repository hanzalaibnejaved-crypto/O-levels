import sqlite3
import os
from datetime import datetime

def get_db_path():
    """Get the database file path"""
    return 'o_levels_platform.db'

def init_db():
    """Initialize the database with required tables"""
    db_path = get_db_path()
    
    # Check if database exists, if not create it
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                grade_level VARCHAR(20),
                school VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        # Subjects table
        cursor.execute('''
            CREATE TABLE subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(10) UNIQUE NOT NULL,
                description TEXT,
                color VARCHAR(7),
                icon VARCHAR(50),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Resources table
        cursor.execute('''
            CREATE TABLE resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                description TEXT,
                resource_type VARCHAR(50) NOT NULL, -- 'notes', 'video', 'questions', 'past_paper'
                file_path VARCHAR(500),
                file_size INTEGER,
                duration INTEGER, -- for videos in minutes
                difficulty VARCHAR(20), -- 'easy', 'medium', 'hard'
                marks INTEGER,
                paper_number INTEGER,
                year INTEGER,
                topic VARCHAR(100),
                uploaded_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                download_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                FOREIGN KEY (subject_id) REFERENCES subjects (id),
                FOREIGN KEY (uploaded_by) REFERENCES users (id)
            )
        ''')
        
        # User progress table
        cursor.execute('''
            CREATE TABLE user_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                resource_id INTEGER,
                progress_type VARCHAR(50), -- 'completed', 'in_progress', 'bookmarked'
                completed BOOLEAN DEFAULT 0,
                score DECIMAL(5,2),
                time_spent INTEGER, -- in minutes
                last_accessed DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (subject_id) REFERENCES subjects (id),
                FOREIGN KEY (resource_id) REFERENCES resources (id)
            )
        ''')
        
        # Tests table
        cursor.execute('''
            CREATE TABLE tests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                subject_id INTEGER NOT NULL,
                paper_number INTEGER,
                difficulty VARCHAR(20),
                total_marks INTEGER,
                time_limit INTEGER, -- in minutes
                question_types TEXT, -- JSON array of question types
                custom_questions TEXT, -- JSON array of question IDs
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_completed BOOLEAN DEFAULT 0,
                score DECIMAL(5,2),
                time_taken INTEGER,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (subject_id) REFERENCES subjects (id)
            )
        ''')
        
        # Questions table
        cursor.execute('''
            CREATE TABLE questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type VARCHAR(50) NOT NULL, -- 'mcq', 'short', 'long'
                options TEXT, -- JSON array for MCQ options
                correct_answer TEXT,
                marks INTEGER,
                difficulty VARCHAR(20),
                topic VARCHAR(100),
                explanation TEXT,
                created_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects (id),
                FOREIGN KEY (created_by) REFERENCES users (id)
            )
        ''')
        
        # User activity table
        cursor.execute('''
            CREATE TABLE user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                activity_type VARCHAR(50) NOT NULL, -- 'login', 'resource_view', 'test_taken', 'progress_update'
                activity_details TEXT,
                activity_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                ip_address VARCHAR(45),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Insert sample subjects
        sample_subjects = [
            ('Mathematics', 'MATH', 'Comprehensive mathematics curriculum', '#ff6b6b', 'calculator'),
            ('Computer Science', 'COMP', 'Programming and computer fundamentals', '#4ecdc4', 'laptop-code'),
            ('Chemistry', 'CHEM', 'Study of elements and compounds', '#45b7d1', 'flask'),
            ('Physics', 'PHYS', 'Fundamental principles of matter and energy', '#ffa726', 'atom'),
            ('English', 'ENG', 'Language skills and literature', '#ba68c8', 'book-open'),
            ('Islamiat', 'ISL', 'Islamic studies and teachings', '#66bb6a', 'mosque'),
            ('Pakistan Studies', 'PST', 'History and geography of Pakistan', '#78909c', 'globe-asia')
        ]
        
        cursor.executemany('''
            INSERT INTO subjects (name, code, description, color, icon) 
            VALUES (?, ?, ?, ?, ?)
        ''', sample_subjects)
        
        # Insert sample admin user
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, full_name, grade_level, school)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@olevels.com', 'pbkdf2:sha256:260000$abc123$hashedpassword', 'Admin User', 'O-Level', 'Demo School'))
        
        conn.commit()
        conn.close()
        print("Database initialized successfully!")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn

def close_db(conn):
    """Close database connection"""
    if conn:
        conn.close()