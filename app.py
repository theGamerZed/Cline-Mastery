from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get('KEY')  

# Database configuration
DATABASE = 'movies.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create movies table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('movie', 'series')),
            genre TEXT,
            release_year INTEGER,
            rating REAL,
            duration TEXT,
            description TEXT,
            poster_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create watchlist table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS watchlist (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER,
            status TEXT CHECK(status IN ('watched', 'watching', 'plan_to_watch')),
            rating INTEGER CHECK(rating >= 1 AND rating <= 10),
            notes TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (movie_id) REFERENCES movies (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()


@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all movies and series
    cursor.execute('''
        SELECT m.*, w.status, w.rating as user_rating 
        FROM movies m 
        LEFT JOIN watchlist w ON m.id = w.movie_id 
        ORDER BY m.created_at DESC
    ''')
    items = cursor.fetchall()
    
    conn.close()
    return render_template('index.html', items=items)


@app.route('/add', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        title = request.form['title']
        item_type = request.form['type']
        genre = request.form['genre']
        release_year = request.form['release_year']
        rating = request.form['rating']
        duration = request.form['duration']
        description = request.form['description']
        poster_url = request.form['poster_url']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO movies (title, type, genre, release_year, rating, duration, description, poster_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (title, item_type, genre, release_year, rating, duration, description, poster_url))
        
        conn.commit()
        conn.close()
        
        flash('Item added successfully!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')


@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        title = request.form['title']
        item_type = request.form['type']
        genre = request.form['genre']
        release_year = request.form['release_year']
        rating = request.form['rating']
        duration = request.form['duration']
        description = request.form['description']
        poster_url = request.form['poster_url']
        
        cursor.execute('''
            UPDATE movies 
            SET title = ?, type = ?, genre = ?, release_year = ?, rating = ?, 
                duration = ?, description = ?, poster_url = ?
            WHERE id = ?
        ''', (title, item_type, genre, release_year, rating, duration, description, poster_url, id))
        
        conn.commit()
        conn.close()
        
        flash('Item updated successfully!', 'success')
        return redirect(url_for('index'))
    
    cursor.execute('SELECT * FROM movies WHERE id = ?', (id,))
    item = cursor.fetchone()
    conn.close()
    
    return render_template('edit.html', item=item)


@app.route('/delete/<int:id>')
def delete_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM movies WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Item deleted successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/watchlist')
def watchlist():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, w.status, w.rating as user_rating, w.notes, w.added_at
        FROM watchlist w
        JOIN movies m ON w.movie_id = m.id
        ORDER BY w.added_at DESC
    ''')
    items = cursor.fetchall()
    
    conn.close()
    return render_template('watchlist.html', items=items)


@app.route('/add_to_watchlist/<int:id>', methods=['POST'])
def add_to_watchlist(id):
    status = request.form['status']
    rating = request.form.get('rating', None)
    notes = request.form.get('notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT OR REPLACE INTO watchlist (movie_id, status, rating, notes)
        VALUES (?, ?, ?, ?)
    ''', (id, status, rating, notes))
    
    conn.commit()
    conn.close()
    
    flash('Added to watchlist!', 'success')
    return redirect(url_for('index'))


@app.route('/remove_from_watchlist/<int:id>')
def remove_from_watchlist(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM watchlist WHERE movie_id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Removed from watchlist!', 'success')
    return redirect(url_for('watchlist'))


@app.route('/search')
def search():
    query = request.args.get('q', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT m.*, w.status, w.rating as user_rating 
        FROM movies m 
        LEFT JOIN watchlist w ON m.id = w.movie_id 
        WHERE m.title LIKE ? OR m.genre LIKE ?
        ORDER BY m.created_at DESC
    ''', (f'%{query}%', f'%{query}%'))
    
    items = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', items=items, search_query=query)


@app.route('/filter/<filter_type>')
def filter_items(filter_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if filter_type == 'movies':
        cursor.execute('''
            SELECT m.*, w.status, w.rating as user_rating 
            FROM movies m 
            LEFT JOIN watchlist w ON m.id = w.movie_id 
            WHERE m.type = 'movie'
            ORDER BY m.created_at DESC
        ''')
    elif filter_type == 'series':
        cursor.execute('''
            SELECT m.*, w.status, w.rating as user_rating 
            FROM movies m 
            LEFT JOIN watchlist w ON m.id = w.movie_id 
            WHERE m.type = 'series'
            ORDER BY m.created_at DESC
        ''')
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
    app.run(debug=True, host='0.0.0.0', port=5000)