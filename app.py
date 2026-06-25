from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import sqlite3
import os
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('KEY', 'fallback-secret-key-change-in-production')

# Database configuration
DATABASE = 'movies.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create movies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('movie', 'series', 'anime')),
            genre TEXT,
            release_year INTEGER,
            rating REAL,
            duration INTEGER,
            episodes INTEGER,
            description TEXT,
            poster_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Create watchlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            movie_id INTEGER,
            status TEXT CHECK(status IN ('watched', 'watching', 'plan_to_watch')),
            rating INTEGER CHECK(rating >= 1 AND rating <= 10),
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
            UNIQUE(user_id, movie_id)
        )
    ''')
    
    conn.commit()
    conn.close()


# --- Authentication Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Auth Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, redirect to home
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        if not email or not password:
            flash('Please fill in all fields.', 'danger')
            return render_template('login.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    # If already logged in, redirect to home
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if not email or not password or not confirm_password:
            flash('Please fill in all fields.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('register.html')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            flash('An account with this email already exists.', 'danger')
            return render_template('register.html')
        
        # Create user
        password_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (email, password_hash) VALUES (?, ?)',
                       (email, password_hash))
        conn.commit()
        conn.close()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# --- Protected Routes ---
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all movies and series for the current user
    cursor.execute('''
        SELECT m.*, w.status, w.rating as user_rating 
        FROM movies m 
        LEFT JOIN watchlist w ON m.id = w.movie_id AND w.user_id = ?
        WHERE m.user_id = ?
        ORDER BY m.created_at DESC
    ''', (session['user_id'], session['user_id']))
    items = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', items=items)


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        title = request.form['title']
        item_type = request.form['type']
        genre = request.form['genre']
        release_year = request.form['release_year']
        rating = request.form['rating']
        duration = request.form.get('duration', type=int)
        episodes = request.form.get('episodes', type=int)
        description = request.form['description']
        poster_url = request.form['poster_url']
        watchlist_action = request.form.get('watchlist_action', 'just_save')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movies (user_id, title, type, genre, release_year, rating, duration, episodes, description, poster_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], title, item_type, genre, release_year, rating, duration, episodes, description, poster_url))
        
        movie_id = cursor.lastrowid
        
        # Handle watchlist action
        if watchlist_action in ('add_to_watchlist', 'mark_watched'):
            status = 'watched' if watchlist_action == 'mark_watched' else 'plan_to_watch'
            cursor.execute('''
                INSERT INTO watchlist (user_id, movie_id, status)
                VALUES (?, ?, ?)
            ''', (session['user_id'], movie_id, status))
        
        conn.commit()
        conn.close()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        item_type = request.form['type']
        genre = request.form['genre']
        release_year = request.form['release_year']
        rating = request.form['rating']
        duration = request.form.get('duration', type=int)
        episodes = request.form.get('episodes', type=int)
        description = request.form['description']
        poster_url = request.form['poster_url']
        watchlist_action = request.form.get('watchlist_action', 'just_save')
        
        cursor.execute('''
            UPDATE movies 
            SET title = ?, type = ?, genre = ?, release_year = ?, rating = ?, 
                duration = ?, episodes = ?, description = ?, poster_url = ?
            WHERE id = ? AND user_id = ?
        ''', (title, item_type, genre, release_year, rating, duration, episodes, description, poster_url, id, session['user_id']))
        
        # Handle watchlist action
        if watchlist_action in ('add_to_watchlist', 'mark_watched'):
            # Check if item already exists in user's watchlist
            cursor.execute('SELECT id FROM watchlist WHERE movie_id = ? AND user_id = ?', (id, session['user_id']))
            existing = cursor.fetchone()
            status = 'watched' if watchlist_action == 'mark_watched' else 'plan_to_watch'
            
            if existing:
                cursor.execute('UPDATE watchlist SET status = ? WHERE movie_id = ? AND user_id = ?', (status, id, session['user_id']))
            else:
                cursor.execute('INSERT INTO watchlist (user_id, movie_id, status) VALUES (?, ?, ?)', (session['user_id'], id, status))
        elif watchlist_action == 'just_save':
            # Remove from user's watchlist if it was there
            cursor.execute('DELETE FROM watchlist WHERE movie_id = ? AND user_id = ?', (id, session['user_id']))
        
        conn.commit()
        conn.close()
        
        flash('Item updated successfully!', 'success')
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM movies WHERE id = ? AND user_id = ?', (id, session['user_id']))
    item = cursor.fetchone()
    conn.close()
    
    if not item:
        flash('Item not found or access denied.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('edit.html', item=item)


@app.route('/delete/<int:id>')
@login_required
def delete_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM movies WHERE id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/watchlist')
@login_required
def watchlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, w.status, w.rating as user_rating, w.notes, w.added_at
        FROM watchlist w
        JOIN movies m ON w.movie_id = m.id
        WHERE w.user_id = ?
        ORDER BY w.added_at DESC
    ''', (session['user_id'],))
    raw_items = cursor.fetchall()
    
    # Calculate watch hours for each item (exclude watched items from total)
    items = []
    total_hours = 0.0
    for item in raw_items:
        item = dict(item)
        if item['type'] == 'movie':
            item['hours'] = round((item['duration'] or 0) / 60, 1)
        else:
            item['hours'] = round((item.get('episodes') or 0) * (item['duration'] or 0) / 60, 1)
        # Mark whether this item is already watched (excluded from total)
        item['is_watched'] = item['status'] == 'watched'
        if not item['is_watched']:
            total_hours += item['hours']
        items.append(item)
    
    total_hours = round(total_hours, 1)
    
    conn.close()
    return render_template('watchlist.html', items=items, total_hours=total_hours)


@app.route('/add_to_watchlist/<int:id>', methods=['POST'])
@login_required
def add_to_watchlist(id):
    status = request.form['status']
    rating = request.form.get('rating', None)
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO watchlist (user_id, movie_id, status, rating, notes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, movie_id) DO UPDATE SET
            status = excluded.status,
            rating = excluded.rating,
            notes = excluded.notes
    ''', (session['user_id'], id, status, rating, notes))
    
    conn.commit()
    conn.close()
    
    flash('Added to watchlist!', 'success')
    return redirect(url_for('index'))


@app.route('/remove_from_watchlist/<int:id>')
@login_required
def remove_from_watchlist(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM watchlist WHERE movie_id = ? AND user_id = ?', (id, session['user_id']))
    conn.commit()
    conn.close()
    
    flash('Removed from watchlist!', 'success')
    return redirect(url_for('watchlist'))


@app.route('/search')
@login_required
def search():
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, w.status, w.rating as user_rating 
        FROM movies m 
        LEFT JOIN watchlist w ON m.id = w.movie_id AND w.user_id = ?
        WHERE (m.title LIKE ? OR m.genre LIKE ?) AND m.user_id = ?
        ORDER BY m.created_at DESC
    ''', (session['user_id'], f'%{query}%', f'%{query}%', session['user_id']))
    
    items = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', items=items, search_query=query)


@app.route('/filter/<filter_type>')
@login_required
def filter_items(filter_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if filter_type == 'movies':
        cursor.execute('''
            SELECT m.*, w.status, w.rating as user_rating 
            FROM movies m 
            LEFT JOIN watchlist w ON m.id = w.movie_id AND w.user_id = ?
            WHERE m.type = 'movie' AND m.user_id = ?
            ORDER BY m.created_at DESC
        ''', (session['user_id'], session['user_id']))
    elif filter_type == 'series':
        cursor.execute('''
            SELECT m.*, w.status, w.rating as user_rating 
            FROM movies m 
            LEFT JOIN watchlist w ON m.id = w.movie_id AND w.user_id = ?
            WHERE m.type = 'series' AND m.user_id = ?
            ORDER BY m.created_at DESC
        ''', (session['user_id'], session['user_id']))
    elif filter_type == 'anime':
        cursor.execute('''
            SELECT m.*, w.status, w.rating as user_rating 
            FROM movies m 
            LEFT JOIN watchlist w ON m.id = w.movie_id AND w.user_id = ?
            WHERE m.type = 'anime' AND m.user_id = ?
            ORDER BY m.created_at DESC
        ''', (session['user_id'], session['user_id']))
    elif filter_type == 'watchlist':
        return redirect(url_for('watchlist'))
    else:
        return redirect(url_for('index'))
    
    items = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', items=items, filter_type=filter_type)


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # Migrate existing database
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Ensure users table exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Check current movies table structure
        cursor.execute("PRAGMA table_info(movies)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add episodes column if it doesn't exist
        if 'episodes' not in columns:
            cursor.execute('ALTER TABLE movies ADD COLUMN episodes INTEGER')
        
        # Add user_id column if it doesn't exist
        if 'user_id' not in columns:
            # Recreate movies table with user_id
            cursor.execute('''
                CREAT   E TABLE IF NOT EXISTS movies_new_migrate (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    title TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('movie', 'series', 'anime')),
                    genre TEXT,
                    release_year INTEGER,
                    rating REAL,
                    duration INTEGER,
                    episodes INTEGER,
                    description TEXT,
                    poster_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            cursor.execute('''
                INSERT INTO movies_new_migrate (id, user_id, title, type, genre, release_year, rating, duration, episodes, description, poster_url, created_at)
                SELECT id, 1, title, type, genre, release_year, rating, duration, episodes, description, poster_url, created_at
                FROM movies
            ''')
            cursor.execute('DROP TABLE movies')
            cursor.execute('ALTER TABLE movies_new_migrate RENAME TO movies')
        
        # Migrate duration from TEXT to INTEGER if needed
        cursor.execute("PRAGMA table_info(movies)")
        columns_after_movies = [col[1] for col in cursor.fetchall()]
        
        if 'duration' in columns_after_movies:
            cursor.execute("PRAGMA table_info(movies)")
            col_info = {col[1]: col for col in cursor.fetchall()}
            duration_type = col_info.get('duration', [None, None, None])[2]
            if duration_type and duration_type.upper() == 'TEXT':
                # Create new table with correct schema and migrate data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movies_new_migrate2 (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        title TEXT NOT NULL,
                        type TEXT NOT NULL CHECK(type IN ('movie', 'series', 'anime')),
                        genre TEXT,
                        release_year INTEGER,
                        rating REAL,
                        duration INTEGER,
                        episodes INTEGER,
                        description TEXT,
                        poster_url TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                ''')
                cursor.execute('''
                    INSERT INTO movies_new_migrate2 (id, user_id, title, type, genre, release_year, rating, duration, description, poster_url, created_at)
                    SELECT id, user_id, title, type, genre, release_year, rating, 
                           CAST(duration AS INTEGER), description, poster_url, created_at
                    FROM movies
                ''')
                cursor.execute('DROP TABLE movies')
                cursor.execute('ALTER TABLE movies_new_migrate2 RENAME TO movies')
        
        # Migrate watchlist table to add user_id
        cursor.execute("PRAGMA table_info(watchlist)")
        watchlist_columns = [col[1] for col in cursor.fetchall()]
        
        if 'user_id' not in watchlist_columns:
            # Recreate watchlist table with user_id
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist_new_migrate (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    movie_id INTEGER,
                    status TEXT CHECK(status IN ('watched', 'watching', 'plan_to_watch')),
                    rating INTEGER CHECK(rating >= 1 AND rating <= 10),
                    notes TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                    FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE,
                    UNIQUE(user_id, movie_id)
                )
            ''')
            cursor.execute('''
                INSERT INTO watchlist_new_migrate (id, user_id, movie_id, status, rating, notes, added_at)
                SELECT id, 1, movie_id, status, rating, notes, added_at
                FROM watchlist
            ''')
            cursor.execute('DROP TABLE watchlist')
            cursor.execute('ALTER TABLE watchlist_new_migrate RENAME TO watchlist')
        
        # Update CHECK constraint to include 'anime' - recreate table if needed
        cursor.execute("PRAGMA table_info(movies)")
        columns_after = [col[1] for col in cursor.fetchall()]
        
        if 'episodes' in columns_after:
            # Check if old CHECK constraint still restricts 'anime'
            cursor.execute("SELECT DISTINCT type FROM movies")
            existing_types = [row[0] for row in cursor.fetchall()]
            if existing_types and all(t not in ('anime',) for t in existing_types):
                # Try inserting a temp value to test constraint
                try:
                    cursor.execute("INSERT INTO movies (title, type, user_id) VALUES ('__test__', 'anime', 1)")
                    cursor.execute("DELETE FROM movies WHERE title = '__test__'")
                except sqlite3.OperationalError as e:
                    if 'CHECK' in str(e) or 'constraint' in str(e):
                        # Recreate table with new CHECK constraint
                        cursor.execute('''
                            CREATE TABLE IF NOT EXISTS movies_new_migrate3 (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                user_id INTEGER NOT NULL,
                                title TEXT NOT NULL,
                                type TEXT NOT NULL CHECK(type IN ('movie', 'series', 'anime')),
                                genre TEXT,
                                release_year INTEGER,
                                rating REAL,
                                duration INTEGER,
                                episodes INTEGER,
                                description TEXT,
                                poster_url TEXT,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                            )
                        ''')
                        cursor.execute('''
                            INSERT INTO movies_new_migrate3 (id, user_id, title, type, genre, release_year, rating, duration, episodes, description, poster_url, created_at)
                            SELECT id, user_id, title, type, genre, release_year, rating, duration, episodes, description, poster_url, created_at
                            FROM movies
                        ''')
                        cursor.execute('DROP TABLE movies')
                        cursor.execute('ALTER TABLE movies_new_migrate3 RENAME TO movies')
        
        conn.commit()
        conn.close()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
