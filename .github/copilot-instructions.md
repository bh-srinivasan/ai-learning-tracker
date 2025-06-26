<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# AI Learning Tracker - Copilot Instructions

## Project Overview

This is a Python Flask web application for tracking personal AI learning progress and providing course recommendations. The app uses SQLite for data storage and Bootstrap for responsive UI.

## Key Architecture Patterns

- **Blueprint-based routing**: Each module (auth, dashboard, learnings) has its own Blueprint
- **Session-based authentication**: User sessions stored server-side
- **Template inheritance**: Base template with extending templates for each page
- **Progressive enhancement**: Start with basic features, build toward advanced recommendations

## Code Style Guidelines

- Use Flask best practices with blueprints for modular organization
- Follow PEP 8 for Python code formatting
- Use descriptive variable names and include type hints where helpful
- Add docstrings for complex functions
- Use Bootstrap classes for consistent UI styling

## Database Patterns

- SQLite with manual connection management using `get_db_connection()`
- Always close database connections after use
- Use parameterized queries to prevent SQL injection
- Foreign key relationships between users and learning entries

## Security Considerations

- Hash passwords using Werkzeug's `generate_password_hash`
- Validate user ownership of learning entries before edit/delete
- Use session management for authentication state
- Sanitize user inputs in forms

## Template Guidelines

- Extend `base.html` for consistent layout and navigation
- Use Bootstrap components for responsive design
- Include meaningful icons with Font Awesome
- Implement proper form validation and error messaging
- Use Jinja2 template filters for data formatting

## Future Development Areas

1. **Course Integration**: Microsoft Learn API integration for course discovery
2. **Recommendation Engine**: Level-based course suggestions
3. **Admin Panel**: Course management and user administration
4. **Analytics**: Learning progress visualization and insights
5. **API Development**: RESTful endpoints for mobile/external access

## Testing Approach

- Test with the two demo users: admin/admin and bharath/bharath
- Verify level progression logic with different entry counts
- Test form validation and error handling
- Ensure proper session management and logout

## Performance Notes

- SQLite is suitable for personal use with limited concurrent users
- Consider pagination for large learning entry lists
- Optimize database queries as data grows
- Cache user level calculations if needed

When suggesting code improvements or new features, prioritize:

1. User experience and intuitive navigation
2. Data integrity and proper validation
3. Scalable architecture for future enhancements
4. Integration readiness for Microsoft services
