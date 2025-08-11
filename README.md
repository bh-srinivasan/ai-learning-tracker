# AI Learning Tracker

A personal productivity web application for tracking and recommending AI learning.

## Features

### 🎯 Core Features
- **AI Learning Tracker**: Manually add AI learning entries with title, description, date, and tags
- **Knowledge Level Assessment**: Automatic level assignment (Beginner → Learner → Intermediate → Expert)
- **User Dashboard**: View learning progress, current level, and recommendations
- **Session-based Authentication**: Secure login/logout functionality

### 👥 User Management
- Two predefined users: `admin` and `bharath` (username = password)
- Session-based authentication
- User-specific learning tracking

### 📊 Progress Tracking
- **Beginner**: 0-4 learning entries
- **Learner**: 5-9 learning entries  
- **Intermediate**: 10-19 learning entries
- **Expert**: 20+ learning entries

## Tech Stack

- **Backend**: Python 3.x + Flask
- **Database**: SQLite
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Authentication**: Session-based with Werkzeug password hashing

## Project Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── ai_learning.db        # SQLite database (auto-created)
├── auth/                 # Authentication module
│   ├── __init__.py
│   └── routes.py
├── dashboard/            # Dashboard views
│   ├── __init__.py
│   └── routes.py
├── learnings/            # Learning tracking
│   ├── __init__.py
│   └── routes.py
├── courses/              # Course management (future)
├── recommendations/      # Recommendations (future)
├── admin/               # Admin functionality (future)
├── templates/           # HTML templates
│   ├── base.html
│   ├── auth/
│   │   └── login.html
│   ├── dashboard/
│   │   └── index.html
│   └── learnings/
│       ├── index.html
│       ├── add.html
│       └── edit.html
└── static/              # CSS, JS, images
```

## Setup & Installation

### Prerequisites
- Python 3.7+
- pip package manager

### Installation Steps

1. **Clone or download the project**
   ```bash
   cd AI_Learning
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Access the application**
   - Open browser to: http://localhost:5000
   - Login with: `admin`/`admin` or `bharath`/`bharath`

## Usage

### Getting Started
1. **Login** with one of the demo accounts
2. **Add Learning Entries** from the dashboard or learnings page
3. **Track Progress** as your level automatically updates
4. **View Dashboard** to see recent activities and progress

### Adding Learning Entries
- Click "Add Learning" from the sidebar or dashboard
- Fill in title (required), description, and tags
- Use descriptive titles and consistent tags for better organization
- Track both formal courses and informal learning

### Level Progression
- Your level automatically updates based on learning entries
- Progress bars show advancement toward next level
- View level requirements in the dashboard stats cards

## Database Schema

### Users Table
- `id`: Primary key
- `username`: Unique username
- `password_hash`: Hashed password
- `level`: Current knowledge level
- `created_at`: Account creation timestamp

### Learning Entries Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `title`: Learning entry title
- `description`: Optional description
- `date_added`: Entry creation timestamp
- `tags`: Comma-separated tags

### Courses Table (Future Implementation)
- `id`: Primary key
- `title`: Course title
- `source`: Course source (Microsoft Learn, etc.)
- `level`: Target level
- `link`: Course URL
- `created_at`: Entry timestamp

## Future Enhancements

### Phase 2: Course Management
- **Course Search & Classification**: Integration with Microsoft Learn and Viva Learning
- **Admin Panel**: Manual course updates and management
- **Course Database**: Store and categorize AI-related courses

### Phase 3: Recommendations
- **Gap Analysis**: Compare user level with available courses
- **Smart Recommendations**: Suggest courses for progression
- **Personalized Learning Paths**: Customized advancement routes

### Phase 4: Advanced Features
- **Microsoft Graph API Integration**: Enhanced Microsoft services integration
- **Automated Course Discovery**: Daily course updates
- **Advanced Analytics**: Learning patterns and insights
- **Export/Import**: Learning data portability

## Development

### Database Compatibility
This application supports dual database backends:
- **Local Development**: SQLite database (`ai_learning.db`)
- **Production**: Azure SQL Database

#### Database Kind Detection
The app automatically detects the database type, but can be overridden:
```bash
# Force specific database type for testing
export DB_KIND=sqlite     # Use SQLite
export DB_KIND=sqlserver  # Use SQL Server/Azure SQL
```

### Azure SQL Database Deployment

#### Prerequisites
- Azure SQL Database provisioned
- Environment variables configured (see Production Deployment)

#### Deploy Compatibility View
Run the following SQL script in Azure SQL Database via Azure Portal Query Editor, Azure Data Studio, or sqlcmd:

```bash
# Using Azure Portal Query Editor:
1. Navigate to your Azure SQL Database in Azure Portal
2. Go to Query Editor
3. Execute: db/migrations/azure/001_create_view_courses_app.sql

# Using Azure Data Studio:
1. Connect to your Azure SQL Database
2. Open: db/migrations/azure/001_create_view_courses_app.sql
3. Execute the script

# Using sqlcmd:
sqlcmd -S your-server.database.windows.net -d your-database -U your-username -P your-password -i db/migrations/azure/001_create_view_courses_app.sql
```

The compatibility view (`dbo.courses_app`) provides a uniform interface between Azure SQL schema and application expectations, mapping:
- `duration` (NVARCHAR) → `duration_hours` (FLOAT)
- `difficulty` or `level` → `difficulty`
- Missing `category` → NULL placeholder

#### Optional: Migrate to Real Columns
For future schema evolution, see `db/migrations/azure/002_optional_real_columns.sql` (do not run until ready to migrate from view-based approach).

### Running in Development Mode
```bash
python app.py
```
- Debug mode is enabled by default
- Application auto-reloads on file changes
- Detailed error messages in browser

### Database Management
- Database auto-initializes on first run
- Default users created automatically
- SQLite file: `ai_learning.db` (local development)
- Azure SQL: Uses `dbo.courses_app` view for compatibility

### Adding New Features
1. Create new modules in appropriate folders
2. Register blueprints in `app.py`
3. Add templates in `templates/` folder
4. Update navigation in `base.html`

## Security Notes

- Session-based authentication
- Password hashing with Werkzeug
- CSRF protection recommended for production
- Environment variables recommended for secrets
- HTTPS recommended for production deployment

## Contributing

This is a personal productivity tool. Future enhancements will focus on:
- Microsoft ecosystem integration
- Enhanced recommendation algorithms
- Advanced progress tracking
- Export/import capabilities

## License

Private project for personal/internal use.
