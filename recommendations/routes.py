# Recommendations routes
from flask import Blueprint

bp = Blueprint('recommendations', __name__)

# Placeholder for future recommendation features
@bp.route('/')
def index():
    return "Recommendations coming soon!"
