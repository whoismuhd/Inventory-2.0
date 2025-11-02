"""Database configuration and initialization"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_db():
    """Initialize database with tables and default data"""
    from models import (
        Item, Request, Notification, Actual, ProjectSite,
        AccessCode, AccessLog, BuildingTypeConfig
    )
    
    db.create_all()
    
    # Create default global admin code if none exists
    # This is the ONLY default access code - project sites must be created manually
    from werkzeug.security import generate_password_hash
    if AccessCode.query.filter_by(code_type='global_admin', project_site=None).count() == 0:
        default_code = 'admin123'
        admin_code = AccessCode(
            code_type='global_admin',
            project_site=None,
            code_hash=generate_password_hash(default_code),  # Default password - CHANGE IN PRODUCTION!
            display_code=default_code  # Store plaintext for admin display
        )
        db.session.add(admin_code)
        db.session.commit()
    
    # Note: Project sites and their access codes are created manually through Admin Settings
    # No default project sites or access codes are created automatically

