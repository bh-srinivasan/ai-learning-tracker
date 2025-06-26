# Production Configuration for Flask App

import os
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Production configuration
    if os.environ.get('FLASK_ENV') == 'production':
        app.config['DEBUG'] = False
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-production-secret-key-here')
        # Use Azure SQL Database or PostgreSQL for production
        app.config['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///ai_learning.db')
    else:
        app.config['DEBUG'] = True
        app.config['SECRET_KEY'] = 'dev-secret-key'
        app.config['DATABASE_URL'] = 'sqlite:///ai_learning.db'
    
    return app

# For Azure App Service
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
