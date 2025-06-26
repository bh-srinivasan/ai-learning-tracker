import os
from app import app

if __name__ == "__main__":
    # Get port from environment variable or default to 8000 for Azure
    port = int(os.environ.get('PORT', 8000))
    
    # Azure requires binding to 0.0.0.0
    app.run(host='0.0.0.0', port=port, debug=False)
