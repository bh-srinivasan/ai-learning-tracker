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

## Safe Repository Cleanup

The `tools/safe_clean.py` script provides intelligent repository cleanup with Flask route-aware in-use detection.

### Features
- **Route-aware scanning**: Loads Flask app in testing mode and crawls GET routes to detect in-use templates, static files, and opened files
- **Upload directory protection**: Static analysis of POST/PUT routes and config keys to identify upload/document directories
- **Safe simulation**: Optional POST route simulation with dummy data to discover dynamic file usage
- **Git-aware**: Never deletes Git-tracked files, works with ignored/untracked files only
- **Age-gated deletion**: Only removes files older than specified days (default: 30)
- **Comprehensive reporting**: Detailed dry-run reports before any deletions
- **Backup creation**: Creates zip backups before applying deletions

### Usage

#### Basic Dry-Run (Safe)
```bash
python tools/safe_clean.py
```
Performs static analysis only, generates report without deletions.

#### Route-Aware Dry-Run
```bash
python tools/safe_clean.py --route-scan
```
Loads Flask app, crawls GET routes, and analyzes in-use assets.

#### Apply with Route Analysis
```bash
python tools/safe_clean.py --route-scan --apply
```
Performs route analysis and applies deletions after confirmation.

#### POST Route Simulation
```bash
python tools/safe_clean.py --route-scan --simulate-post --post-allow "^/test-upload$" --apply
```
Includes safe simulation of allowed POST routes to detect upload patterns.

### Flags

#### Main Operation
- `--apply`: Apply deletions (default: dry-run only)
- `--age-days N`: Only delete files older than N days (default: 30)
- `--report FILE`: Custom report filename

#### Route Scanning
- `--route-scan`: Enable Flask route scanning for in-use detection
- `--follow-redirects`: Follow redirects during route crawling
- `--include-routes REGEX`: Pattern for routes to include
- `--exclude-routes REGEX`: Pattern for routes to exclude (default: admin/debug/internal)

#### POST Simulation
- `--simulate-post`: Enable safe POST route simulation (requires --post-allow)
- `--post-allow REGEX`: Regex pattern for POST routes allowed for simulation

#### Pruning Options
- `--prune-uploads {none,artifacts,all}`: Upload directory pruning mode (default: none)
- `--prune-tests {none,artifacts,orphaned,all}`: Test directory pruning mode (default: none)

#### Patterns
- `--include-pattern PATTERN`: Additional patterns to include for deletion
- `--exclude-pattern PATTERN`: Additional patterns to exclude from deletion

### Safety Features

1. **Protected Paths**: Never deletes critical files like `app.py`, `templates/`, `static/`, `.env`, etc.
2. **Git Integration**: Only considers Git ignored and untracked files as deletion candidates
3. **In-Use Detection**: Protects files discovered through route crawling and static analysis
4. **Confirmations**: Requires typed confirmations ("DELETE", "DELETE UPLOADS", "DELETE TESTS")
5. **Backups**: Creates zip backups before any destructive operations
6. **Large File Handling**: Skips files >100MB from backups, lists them separately

### Manual Git Cleanup (Alternative)

For manual cleanup without the tool:

```bash
# Preview ignored files only (safer)
git clean -ndX

# Preview ignored + untracked files (more aggressive)
git clean -ndx

# Apply ignored files cleanup (after review)
git clean -fdX

# Apply ignored + untracked cleanup (after careful review)
git clean -fdx
```

⚠️ **WARNING**: Manual `git clean` commands can be destructive. Always use `-n` (dry-run) first and create backups. The `safe_clean.py` tool is recommended for intelligent cleanup.

### Examples

```bash
# Safe dry-run with route analysis
python tools/safe_clean.py --route-scan

# Apply cleanup with 7-day age limit
python tools/safe_clean.py --route-scan --age-days 7 --apply

# Include specific patterns
python tools/safe_clean.py --include-pattern "*.tmp" --include-pattern "*.cache" --apply

# Exclude specific patterns  
python tools/safe_clean.py --exclude-pattern "important_temp/*" --apply
```

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
