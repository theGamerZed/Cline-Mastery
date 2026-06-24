# Movie & Series Tracker

A modern, responsive web application for tracking movies and TV series built with Flask, SQLite, HTML/CSS, and Bootstrap.

## Features

- **📽️ Movie & Series Management**: Add, edit, and delete movies and TV series
- **📋 Watchlist Tracking**: Track what you want to watch, are currently watching, or have completed
- **⭐ Rating System**: Rate movies/series and track your personal ratings
- **🔍 Search & Filter**: Quickly find content by title or genre
- **📊 Statistics**: View watchlist statistics and progress
- **📱 Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **🎨 Modern UI**: Clean, intuitive interface with smooth animations

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Bootstrap 5
- **Icons**: Bootstrap Icons
- **Styling**: Custom CSS with modern design patterns

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. **Clone or download the project files**
   ```bash
   git clone <repository-url>
   cd movie-tracker
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## Project Structure

```
movie-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── movies.db             # SQLite database (created automatically)
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html        # Base template with navigation
│   ├── index.html       # Main page with all movies/series
│   ├── add.html         # Add new item form
│   ├── edit.html        # Edit item form
│   └── watchlist.html   # Watchlist view
└── static/              # Static files
    └── css/
        └── style.css    # Custom styles
```

## Usage Guide

### Adding Content

1. Click "Add New" in the navigation bar
2. Fill in the required fields (title and type)
3. Add optional details like genre, release year, rating, etc.
4. Click "Save Item"

### Managing Your Collection

- **View All**: See all movies and series on the home page
- **Filter**: Use filter buttons to show only movies, series, or watchlist items
- **Search**: Use the search bar to find specific titles or genres
- **Edit**: Click the "Edit" button to modify item details
- **Delete**: Click the "Delete" button to remove an item (with confirmation)

### Watchlist Management

1. **Add to Watchlist**: Click "Add to Watchlist" on any item
   - Choose status: Plan to Watch, Currently Watching, or Watched
   - Add your personal rating (1-10)
   - Include optional notes
2. **View Watchlist**: Click "Watchlist" in the navigation
3. **Remove from Watchlist**: Click "Remove" on any watchlist item

### Statistics

The watchlist page shows your viewing statistics:
- 📌 Plan to Watch
- ⏳ Currently Watching  
- ✅ Completed

## Database Schema

### Movies Table
- `id`: Primary key
- `title`: Movie/series title
- `type`: 'movie' or 'series'
- `genre`: Genre category
- `release_year`: Release year
- `rating`: Rating (1-10)
- `duration`: Runtime or episode count
- `description`: Description/summary
- `poster_url`: Poster image URL
- `created_at`: Timestamp

### Watchlist Table
- `id`: Primary key
- `movie_id`: Foreign key to movies table
- `status`: 'watched', 'watching', or 'plan_to_watch'
- `rating`: Personal rating (1-10)
- `notes`: Personal notes
- `added_at`: Timestamp

## Customization

### Styling

Edit `static/css/style.css` to customize:
- Colors and themes
- Animations and transitions
- Layout and spacing
- Responsive breakpoints

### Database

The SQLite database is automatically created on first run. To reset:

1. Stop the application
2. Delete `movies.db`
3. Restart the application

### Configuration

Key settings in `app.py`:
- `DATABASE`: Database file name
- `app.secret_key`: Session security key (change in production)
- `debug`: Debug mode (set to False in production)
- `host`/`port`: Server binding settings

## Development

### Adding New Features

1. **Backend**: Add routes in `app.py`
2. **Frontend**: Create/modify templates in `templates/`
3. **Styling**: Update `static/css/style.css`
4. **Database**: Modify `init_db()` function for schema changes

### API Endpoints

- `GET /` - Home page with all items
- `GET /add` - Add item form
- `POST /add` - Create new item
- `GET /edit/<id>` - Edit item form
- `POST /edit/<id>` - Update item
- `GET /delete/<id>` - Delete item
- `GET /watchlist` - Watchlist view
- `POST /add_to_watchlist/<id>` - Add to watchlist
- `GET /remove_from_watchlist/<id>` - Remove from watchlist
- `GET /search?q=<query>` - Search items
- `GET /filter/<type>` - Filter by type

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

- Lightweight SQLite database
- Efficient SQL queries with JOINs
- Minimal JavaScript dependency
- Optimized CSS with modern features
- Responsive images and lazy loading ready

## Security

- CSRF protection via Flask-WTF (can be added)
- SQL injection prevention using parameterized queries
- XSS protection via Jinja2 auto-escaping
- Secure session management

## Troubleshooting

### Common Issues

**Database locked error**: Ensure only one instance is running
**Port 5000 in use**: Change port in `app.py` or kill existing process
**Template not found**: Check templates directory structure
**Static files not loading**: Verify static directory and URL paths

### Debug Mode

Enable debug mode in development:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Future Enhancements

Potential features to add:
- User authentication system
- Import/export functionality (CSV/JSON)
- API for mobile app integration
- Advanced filtering and sorting
- Recommendation engine
- Watch history tracking
- Multiple watchlists
- Social sharing features

## License

This project is open source and available for modification and distribution.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues, questions, or suggestions, please open an issue in the project repository.

---

**Happy Watching! 🎬**