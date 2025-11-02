"""Database models for Inventory Management System"""
from database import db
from datetime import datetime

class Item(db.Model):
    """Inventory items"""
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(100), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # 'materials' or 'labour'
    unit = db.Column(db.String(50), nullable=True)
    qty = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    unit_cost = db.Column(db.Numeric(10, 2), nullable=True)
    budget = db.Column(db.String(200), nullable=True)
    section = db.Column(db.String(200), nullable=True)
    grp = db.Column(db.String(100), nullable=True)
    building_type = db.Column(db.String(50), nullable=True)
    project_site = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def amount(self):
        """Calculate total amount"""
        if self.qty and self.unit_cost:
            return float(self.qty) * float(self.unit_cost)
        return 0.0

class Request(db.Model):
    """Item requests"""
    __tablename__ = 'requests'
    
    id = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.utcnow)
    section = db.Column(db.String(50), nullable=False)  # 'materials' or 'labour'
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    qty = db.Column(db.Numeric(10, 2), nullable=False)
    requested_by = db.Column(db.String(100), nullable=False)
    note = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Approved', 'Rejected'
    approved_by = db.Column(db.String(100), nullable=True)
    current_price = db.Column(db.Numeric(10, 2), nullable=True)
    building_type = db.Column(db.String(50), nullable=True)
    budget = db.Column(db.String(200), nullable=True)
    project_site = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    item = db.relationship('Item', backref='requests')

class Notification(db.Model):
    """System notifications"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, nullable=True)
    request_id = db.Column(db.Integer, db.ForeignKey('requests.id', ondelete='CASCADE'), nullable=True)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    request = db.relationship('Request', backref='notifications')

class Actual(db.Model):
    """Actual costs and quantities"""
    __tablename__ = 'actuals'
    
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    actual_qty = db.Column(db.Numeric(10, 2), nullable=False)
    actual_cost = db.Column(db.Numeric(10, 2), nullable=False)
    actual_date = db.Column(db.String(50), nullable=True)
    recorded_by = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    project_site = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    item = db.relationship('Item', backref='actuals')

class ProjectSite(db.Model):
    """Project sites"""
    __tablename__ = 'project_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AccessCode(db.Model):
    """Access codes for authentication"""
    __tablename__ = 'access_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    code_type = db.Column(db.String(50), nullable=False)  # 'global_admin', 'admin', 'user'
    project_site = db.Column(db.String(100), nullable=True)
    code_hash = db.Column(db.String(200), nullable=False)
    display_code = db.Column(db.String(100), nullable=True)  # Plaintext for admin display only
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AccessLog(db.Model):
    """Access log for audit trail"""
    __tablename__ = 'access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(100), nullable=True)
    role = db.Column(db.String(50), nullable=True)
    access_code = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False)  # 'Success' or 'Failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    """User model (for reference, though we use session-based auth)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    project_site = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class BuildingTypeConfig(db.Model):
    """Building type configurations (blocks and units per building type)"""
    __tablename__ = 'building_type_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    building_type = db.Column(db.String(50), nullable=False)  # Flats, Terraces, etc.
    blocks = db.Column(db.Integer, nullable=False, default=0)
    units_per_block = db.Column(db.Integer, nullable=False, default=0)
    notes = db.Column(db.Text, nullable=True)
    project_site = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

