@echo off
echo ========================================
echo FLASK APP - ADMIN ROUTES FIXED
echo ========================================

cd /d "c:\Users\bhsrinivasan\Downloads\Learning\Vibe Coding\AI_Learning"

echo Activating virtual environment...
call .venv\Scripts\activate.bat

echo Starting Flask server...
echo.
echo ADMIN ROUTES FIX APPLIED:
echo   ✅ Admin navigation routes added
echo   ✅ Search Courses functionality working
echo   ✅ Course management functions added
echo   ✅ Custom password setting for users restored
echo.
echo ADMIN CAPABILITIES:
echo   - View and manage users
echo   - Set custom passwords for individual users
echo   - Add/edit/delete courses
echo   - Search and import courses
echo.
echo USER DATA VERIFICATION:
echo   - Run quick_check.py to verify user data integrity
echo   - Individual password setting works via admin panel
echo.
echo Open your browser to:
echo   http://localhost:5000/login
echo.
echo Test admin navigation: Users, Courses, Search
echo Press Ctrl+C to stop the server
echo ========================================

python app.py

pause
