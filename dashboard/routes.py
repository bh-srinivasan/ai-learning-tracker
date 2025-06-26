from flask import Blueprint, render_template, session, redirect, url_for, flash, request
import sqlite3

dashboard_bp = Blueprint('dashboard', __name__)

def get_db_connection():
    conn = sqlite3.connect('ai_learning.db')
    conn.row_factory = sqlite3.Row
    return conn

def calculate_user_level(user_id):
    """Calculate user level based on points earned and admin settings"""
    conn = get_db_connection()
    user_points = conn.execute('SELECT points FROM users WHERE id = ?', (user_id,)).fetchone()['points']
    
    # Get level settings from database
    level_settings = conn.execute('''
        SELECT level_name, points_required 
        FROM level_settings 
        ORDER BY points_required DESC
    ''').fetchall()
    
    conn.close()
    
    # Find the appropriate level based on points
    for level in level_settings:
        if user_points >= level['points_required']:
            return level['level_name']
    
    return 'Beginner'  # fallback

def update_user_points_from_courses(user_id):
    """Update user points based on completed courses"""
    conn = get_db_connection()
    
    # Calculate total points from completed courses
    total_points = conn.execute('''
        SELECT COALESCE(SUM(c.points), 0) as total
        FROM user_courses uc
        JOIN courses c ON uc.course_id = c.id
        WHERE uc.user_id = ? AND uc.completed = 1
    ''', (user_id,)).fetchone()['total']
    
    # Update user points
    conn.execute('UPDATE users SET points = ? WHERE id = ?', (total_points, user_id))
    conn.commit()
    
    # Update level based on points
    new_level = calculate_user_level(user_id)
    conn.execute('UPDATE users SET level = ? WHERE id = ?', (new_level, user_id))
    conn.commit()
    
    conn.close()
    session['user_level'] = new_level
    return new_level, total_points

def update_user_level(user_id):
    """Update user level in database based on points"""
    new_level, total_points = update_user_points_from_courses(user_id)
    return new_level

def calculate_progress_percentage(current_level, user_points):
    """Calculate progress percentage toward next level based on points and admin settings"""
    conn = get_db_connection()
    
    # Get level settings from database
    level_settings = conn.execute('''
        SELECT level_name, points_required 
        FROM level_settings 
        ORDER BY points_required ASC
    ''').fetchall()
    
    conn.close()
    
    # Find current and next level
    current_points = 0
    next_points = None
    
    for i, level in enumerate(level_settings):
        if level['level_name'] == current_level:
            current_points = level['points_required']
            if i + 1 < len(level_settings):
                next_points = level_settings[i + 1]['points_required']
            break
    
    if next_points is None:
        return 100  # Already at max level
    
    progress = min((user_points / next_points * 100), 100)
    return int(progress)

def get_next_level_info(current_level):
    """Get information about the next level based on admin settings"""
    conn = get_db_connection()
    
    # Get level settings from database
    level_settings = conn.execute('''
        SELECT level_name, points_required 
        FROM level_settings 
        ORDER BY points_required ASC
    ''').fetchall()
    
    conn.close()
    
    # Find next level
    for i, level in enumerate(level_settings):
        if level['level_name'] == current_level:
            if i + 1 < len(level_settings):
                next_level = level_settings[i + 1]
                return f"{next_level['level_name']} ({next_level['points_required']}+ points)"
            break
    
    return "You've reached the top!"

@dashboard_bp.route('/dashboard')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # If admin, redirect to admin dashboard
    if session.get('username') == 'admin':
        return redirect(url_for('admin.index'))
    
    user_id = session['user_id']
    
    # Update user level based on current points from completed courses
    current_level = update_user_level(user_id)
    
    # Get user points
    conn = get_db_connection()
    user_points = conn.execute('SELECT points FROM users WHERE id = ?', (user_id,)).fetchone()['points']
    
    # For regular users, show their own + global learnings
    recent_entries = conn.execute('''
        SELECT * FROM learning_entries 
        WHERE (user_id = ? OR is_global = 1)
        ORDER BY date_added DESC 
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Get available courses for user
    available_courses = conn.execute('''
        SELECT c.*, 
               CASE WHEN uc.completed IS NOT NULL THEN uc.completed ELSE 0 END as completed
        FROM courses c
        LEFT JOIN user_courses uc ON c.id = uc.course_id AND uc.user_id = ?
        ORDER BY c.level, c.points DESC
        LIMIT 5
    ''', (user_id,)).fetchall()
    
    # Calculate progress percentage based on points
    progress_percentage = calculate_progress_percentage(current_level, user_points)
    next_level_info = get_next_level_info(current_level)
    
    conn.close()
    
    return render_template('dashboard/index.html', 
                         recent_entries=recent_entries,
                         user_points=user_points,
                         current_level=current_level,
                         recommended_courses=available_courses,
                         progress_percentage=progress_percentage,
                         next_level_info=next_level_info)

@dashboard_bp.route('/enroll_course/<int:course_id>', methods=['POST'])
def enroll_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        # Check if already enrolled
        existing = conn.execute('''
            SELECT id FROM user_courses 
            WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id)).fetchone()
        
        if existing:
            flash('You are already enrolled in this course!', 'info')
        else:
            # Enroll user in course
            conn.execute('''
                INSERT INTO user_courses (user_id, course_id)
                VALUES (?, ?)
            ''', (user_id, course_id))
            conn.commit()
            flash('Successfully enrolled in course!', 'success')
    except Exception as e:
        flash('Error enrolling in course. Please try again.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/complete_course/<int:course_id>', methods=['POST'])
def complete_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        # Mark course as completed
        conn.execute('''
            UPDATE user_courses 
            SET completed = 1, completion_date = CURRENT_TIMESTAMP
            WHERE user_id = ? AND course_id = ?
        ''', (user_id, course_id))
        
        # If not enrolled, enroll and complete
        if conn.rowcount == 0:
            conn.execute('''
                INSERT INTO user_courses (user_id, course_id, completed, completion_date)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ''', (user_id, course_id))
        
        conn.commit()
        
        # Update user points and level
        update_user_points_from_courses(user_id)
        
        flash('Course completed! Points have been awarded.', 'success')
    except Exception as e:
        flash('Error completing course. Please try again.', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    if request.method == 'POST':
        # User can only update their selected level
        user_selected_level = request.form.get('user_selected_level')
        
        if user_selected_level in ['Beginner', 'Learner', 'Intermediate', 'Expert']:
            try:
                conn.execute('''
                    UPDATE users 
                    SET user_selected_level = ? 
                    WHERE id = ?
                ''', (user_selected_level, user_id))
                conn.commit()
                flash(f'Profile updated! Your expertise level set to {user_selected_level}', 'success')
            except Exception as e:
                flash(f'Error updating profile: {str(e)}', 'error')
        else:
            flash('Invalid expertise level selected', 'error')
    
    # Get user data
    user = conn.execute('''
        SELECT username, level, points, user_selected_level, created_at 
        FROM users 
        WHERE id = ?
    ''', (user_id,)).fetchone()
    
    # Get user's learning stats
    total_learnings = conn.execute('''
        SELECT COUNT(*) as count 
        FROM learning_entries 
        WHERE user_id = ? AND is_global = 0
    ''', (user_id,)).fetchone()['count']
    
    completed_courses = conn.execute('''
        SELECT COUNT(*) as count 
        FROM user_courses 
        WHERE user_id = ? AND completed = 1
    ''', (user_id,)).fetchone()['count']
    
    enrolled_courses = conn.execute('''
        SELECT COUNT(*) as count 
        FROM user_courses 
        WHERE user_id = ? AND completed = 0
    ''', (user_id,)).fetchone()['count']
    
    conn.close()
    
    return render_template('dashboard/profile.html',
                         user=user,
                         total_learnings=total_learnings,
                         completed_courses=completed_courses,
                         enrolled_courses=enrolled_courses)

@dashboard_bp.route('/add_course', methods=['GET', 'POST'])
def add_course():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Admin users should use admin panel for adding courses
    if session.get('username') == 'admin':
        flash('Admin users should use the admin panel to add courses.', 'info')
        return redirect(url_for('admin.add_course'))
    
    if request.method == 'POST':
        title = request.form['title']
        source = request.form['source']
        course_url = request.form['course_url']
        description = request.form['description']
        completion_date = request.form['completion_date'] if request.form['completion_date'] else None
        user_id = session['user_id']
        
        if title and source and course_url:
            conn = get_db_connection()
            try:
                # Check for duplicates by title and URL for this user
                existing_title = conn.execute('''
                    SELECT id FROM user_personal_courses 
                    WHERE user_id = ? AND LOWER(title) = LOWER(?)
                ''', (user_id, title)).fetchone()
                
                existing_url = conn.execute('''
                    SELECT id FROM user_personal_courses 
                    WHERE user_id = ? AND course_url = ?
                ''', (user_id, course_url)).fetchone()
                
                if existing_title:
                    flash('You already have a course with this title.', 'error')
                elif existing_url:
                    flash('You already have a course with this URL.', 'error')
                else:
                    conn.execute('''
                        INSERT INTO user_personal_courses (user_id, title, source, course_url, description, completion_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (user_id, title, source, course_url, description, completion_date))
                    conn.commit()
                    flash(f'Course "{title}" added successfully!', 'success')
                    return redirect(url_for('dashboard.my_courses'))
            except Exception as e:
                flash(f'Error adding course: {str(e)}', 'error')
            finally:
                conn.close()
        else:
            flash('Course title, source, and URL are required.', 'error')
    
    return render_template('dashboard/add_course.html')

@dashboard_bp.route('/my_courses')
def my_courses():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Admin users should use admin panel
    if session.get('username') == 'admin':
        return redirect(url_for('admin.courses'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get user's personal courses
    personal_courses = conn.execute('''
        SELECT * FROM user_personal_courses 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    
    conn.close()
    
    return render_template('dashboard/my_courses.html', courses=personal_courses)

@dashboard_bp.route('/edit_course/<int:course_id>', methods=['GET', 'POST'])
def edit_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    # Get the course and verify ownership
    course = conn.execute('''
        SELECT * FROM user_personal_courses 
        WHERE id = ? AND user_id = ?
    ''', (course_id, user_id)).fetchone()
    
    if not course:
        flash('Course not found or access denied', 'error')
        return redirect(url_for('dashboard.my_courses'))
    
    if request.method == 'POST':
        title = request.form['title']
        source = request.form['source']
        course_url = request.form['course_url']
        description = request.form['description']
        completion_date = request.form['completion_date'] if request.form['completion_date'] else None
        
        if title and source and course_url:
            try:
                # Check for duplicates (excluding current course)
                existing = conn.execute('''
                    SELECT id FROM user_personal_courses 
                    WHERE user_id = ? AND LOWER(title) = LOWER(?) AND id != ?
                ''', (user_id, title, course_id)).fetchone()
                
                if existing:
                    flash('You already have a course with this title.', 'error')
                else:
                    conn.execute('''
                        UPDATE user_personal_courses 
                        SET title = ?, source = ?, course_url = ?, description = ?, completion_date = ?
                        WHERE id = ? AND user_id = ?
                    ''', (title, source, course_url, description, completion_date, course_id, user_id))
                    conn.commit()
                    flash('Course updated successfully!', 'success')
                    return redirect(url_for('dashboard.my_courses'))
            except Exception as e:
                flash(f'Error updating course: {str(e)}', 'error')
        else:
            flash('Course title, source, and URL are required.', 'error')
    
    conn.close()
    return render_template('dashboard/edit_course.html', course=course)

@dashboard_bp.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        # Get course title for confirmation
        course = conn.execute('''
            SELECT title FROM user_personal_courses 
            WHERE id = ? AND user_id = ?
        ''', (course_id, user_id)).fetchone()
        
        if not course:
            flash('Course not found or access denied.', 'error')
        else:
            # Delete the course
            conn.execute('''
                DELETE FROM user_personal_courses 
                WHERE id = ? AND user_id = ?
            ''', (course_id, user_id))
            conn.commit()
            flash(f'Course "{course["title"]}" deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting course: {str(e)}', 'error')
    finally:
        conn.close()
    
    return redirect(url_for('dashboard.my_courses'))
