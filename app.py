"""
Istrom Inventory Management System
A Flask-based inventory management system for construction projects
"""
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import os
import csv
import io
import uuid
from functools import wraps
from database import db, init_db
from models import (
    Item, Request, Notification, Actual, ProjectSite, 
    AccessCode, AccessLog, User
)
from routes import (
    manual_entry, download_budget_view, inventory, edit_item, delete_item, delete_all_inventory,
    make_request, review_history, approve_request, reject_request, delete_request, approve_reject_by_id,
    budget_summary, save_building_config, actuals, admin_settings, update_global_admin_code, update_project_site_code,
    add_project_site, edit_project_site, delete_project_site, switch_project_site, access_logs, clear_access_logs,
    notifications, mark_notification_read, delete_notification, check_notifications
)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration - supports both SQLite (local) and PostgreSQL (production)
database_url = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
if database_url:
    # Render provides DATABASE_URL, but SQLAlchemy expects SQLALCHEMY_DATABASE_URI
    # Convert postgres:// to postgresql:// if needed (for newer SQLAlchemy)
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Default to SQLite for local development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Initialize database tables on app startup (works with gunicorn)
# This ensures tables exist before any requests are processed
with app.app_context():
    try:
        db.create_all()
        init_db()
    except Exception as e:
        # Don't crash if database connection fails during startup
        # Will retry on first request
        print(f"Initial database setup: {e}")

# Template filters
@app.template_filter('format_currency')
def format_currency_filter(amount):
    from utils import format_currency
    return format_currency(amount)

@app.template_filter('format_number')
def format_number_filter(num):
    try:
        return f"{int(num):,}"
    except (ValueError, TypeError):
        return str(num)

# Context processor to make project sites available to all templates
@app.context_processor
def inject_project_sites():
    from models import ProjectSite
    try:
        # Only query if database is initialized and tables exist
        return dict(project_sites=ProjectSite.query.all())
    except Exception:
        # Return empty list if database isn't ready yet (during startup)
        return dict(project_sites=[])

# Constants
PROPERTY_TYPES = ['Flats', 'Terraces', 'Semi-detached', 'Fully-detached']
CONSTRUCTION_SECTIONS = [
    "SUBSTRUCTURE (GROUND TO DPC LEVEL)",
    "SUBSTRUCTURE (EXCAVATION TO DPC LEVEL)",
    "TERRACES (6-UNITS) DPC(TERRACE SUBSTRUCTURE)",
    "SUPERSTRUCTURE: GROUND FLOOR; (COLUMN, LINTEL AND BLOCK WORK)",
    "SUPERSTRUCTURE, GROUND FLOOR; (SLAB,BEAMS AND STAIR CASE)",
    "SUPERSTRUCTURE, FIRST FLOOR; (COLUMN, LINTEL AND BLOCK WORK)",
    "SUPERSTRUCTURE FIRST FLOOR SLAB WORK (SLAB, BEAMS & STAIRCASE)",
    "SUPERSTRUCTURE, 1ST FLOOR; (COLUMN, LINTEL, BLOCK WORK AND LIFT SHIFT)"
]
SUBGROUPS = {
    '1-2': ['General Materials', 'Woods', 'Plumbings', 'Irons', 'Labour'],
    '3-20': ['General Materials', 'Woods', 'Plumbings', 'Irons', 'Labour', 'Electrical', 'Mechanical']
}
MAX_BUDGET_NUM = 20

def require_login(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Redirect to login or dashboard"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        access_code = request.form.get('access_code', '').strip()
        
        if not access_code:
            return render_template('login.html', error='Access code is required')
        
        # Check global admin code
        global_admin = AccessCode.query.filter_by(
            code_type='global_admin',
            project_site=None
        ).first()
        
        if global_admin and check_password_hash(global_admin.code_hash, access_code):
            # If there's an existing session and user hasn't confirmed override, warn them
            if existing_session and not override_session:
                return render_template('login.html', 
                    error=None,
                    existing_session=existing_session,
                    new_login='Global Administrator',
                    access_code=access_code)
            
            # Clear old session completely before setting new one
            session.clear()
            session['user_id'] = global_admin.id
            session['user_role'] = 'admin'
            session['user_name'] = 'Global Administrator'
            session['project_site'] = None
            session['is_global_admin'] = True
            # Generate unique session token for tab detection
            session['session_token'] = str(uuid.uuid4())
            
            # Log access
            log = AccessLog(
                user=session['user_name'],
                role='admin',
                access_code=access_code[:4] + '****',
                status='Success'
            )
            db.session.add(log)
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        
        # Check project site codes (single access code per site)
        project_sites = ProjectSite.query.all()
        for site in project_sites:
            site_code = AccessCode.query.filter_by(
                code_type='project_site',
                project_site=site.name
            ).first()
            
            if site_code and check_password_hash(site_code.code_hash, access_code):
                # If there's an existing session and user hasn't confirmed override, warn them
                if existing_session and not override_session:
                    return render_template('login.html', 
                        error=None,
                        existing_session=existing_session,
                        new_login=f'Admin - {site.name}',
                        access_code=access_code)
                
                # Clear old session completely before setting new one
                session.clear()
                session['user_id'] = site_code.id
                session['user_role'] = 'project_site_admin'  # Single code gives admin access to that site
                session['user_name'] = f'Admin - {site.name}'
                session['project_site'] = site.name
                session['assigned_project_site'] = site.name  # Permanently assigned, cannot be changed
                session['is_global_admin'] = False
                # Generate unique session token for tab detection
                session['session_token'] = str(uuid.uuid4())
                
                log = AccessLog(
                    user=session['user_name'],
                    role='admin',
                    access_code=access_code[:4] + '****',
                    status='Success'
                )
                db.session.add(log)
                db.session.commit()
                
                return redirect(url_for('dashboard'))
        
        # Failed login
        log = AccessLog(
            user='Unknown',
            role='unknown',
            access_code=access_code[:4] + '****',
            status='Failed'
        )
        db.session.add(log)
        db.session.commit()
        
        return render_template('login.html', error='Invalid access code', existing_session=existing_session)
    
    return render_template('login.html', existing_session=existing_session)

@app.route('/logout')
def logout():
    """Logout and clear session"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/api/session_info')
def session_info():
    """API endpoint to get current session information"""
    if 'user_id' not in session:
        return jsonify({'logged_in': False})
    
    return jsonify({
        'logged_in': True,
        'session_token': session.get('session_token'),
        'user_role': session.get('user_role'),
        'is_global_admin': session.get('is_global_admin'),
        'project_site': session.get('project_site')
    })

@app.route('/dashboard')
@require_login
def dashboard():
    """Main dashboard - redirects to tab based on query param"""
    tab = request.args.get('tab', 'manual_entry')
    return redirect(url_for(tab))

# Register all routes
app.add_url_rule('/manual_entry', 'manual_entry', manual_entry, methods=['GET', 'POST'])
app.add_url_rule('/download_budget_view', 'download_budget_view', download_budget_view)
app.add_url_rule('/inventory', 'inventory', inventory)
app.add_url_rule('/edit_item/<int:item_id>', 'edit_item', edit_item, methods=['GET', 'POST'])
app.add_url_rule('/delete_item/<int:item_id>', 'delete_item', delete_item, methods=['GET', 'POST'])
app.add_url_rule('/delete_all_inventory', 'delete_all_inventory', delete_all_inventory, methods=['POST'])
app.add_url_rule('/make_request', 'make_request', make_request, methods=['GET', 'POST'])
app.add_url_rule('/review_history', 'review_history', review_history)
app.add_url_rule('/approve_request/<int:request_id>', 'approve_request', approve_request)
app.add_url_rule('/reject_request/<int:request_id>', 'reject_request', reject_request)
app.add_url_rule('/delete_request/<int:request_id>', 'delete_request', delete_request)
app.add_url_rule('/approve_reject_by_id', 'approve_reject_by_id', approve_reject_by_id, methods=['POST'])
app.add_url_rule('/budget_summary', 'budget_summary', budget_summary, methods=['GET'])
app.add_url_rule('/save_building_config', 'save_building_config', save_building_config, methods=['POST'])
app.add_url_rule('/actuals', 'actuals', actuals)
app.add_url_rule('/admin_settings', 'admin_settings', admin_settings)
app.add_url_rule('/update_global_admin_code', 'update_global_admin_code', update_global_admin_code, methods=['POST'])
app.add_url_rule('/update_project_site_code', 'update_project_site_code', update_project_site_code, methods=['POST'])
app.add_url_rule('/add_project_site', 'add_project_site', add_project_site, methods=['POST'])
app.add_url_rule('/edit_project_site', 'edit_project_site', edit_project_site, methods=['POST'])
app.add_url_rule('/delete_project_site', 'delete_project_site', delete_project_site, methods=['GET', 'POST'])
app.add_url_rule('/switch_project_site', 'switch_project_site', switch_project_site, methods=['POST'])
app.add_url_rule('/access_logs', 'access_logs', access_logs)
app.add_url_rule('/clear_access_logs', 'clear_access_logs', clear_access_logs, methods=['POST'])
app.add_url_rule('/notifications', 'notifications', notifications)
app.add_url_rule('/mark_notification_read/<int:notification_id>', 'mark_notification_read', mark_notification_read, methods=['POST'])
app.add_url_rule('/delete_notification/<int:notification_id>', 'delete_notification', delete_notification, methods=['GET', 'POST'])
app.add_url_rule('/api/check_notifications', 'check_notifications', check_notifications)

if __name__ == '__main__':
    with app.app_context():
        init_db()
    # Only run development server locally
    # Production uses gunicorn (see DEPLOYMENT.md for Render setup)
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=False, port=port, host='0.0.0.0')

