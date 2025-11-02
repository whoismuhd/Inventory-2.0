"""Route handlers for all application tabs"""
from flask import render_template, request, redirect, url_for, session, jsonify, send_file, flash
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import csv
import io
from functools import wraps
from database import db
from models import (
    Item, Request, Notification, Actual, ProjectSite,
    AccessCode, AccessLog, BuildingTypeConfig
)
from utils import (
    generate_budget_options, normalize_budget, match_budget_filter,
    format_currency, calculate_line_amount, determine_group_from_category_and_budget,
    extract_budget_parts, PROPERTY_TYPES
)

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
MAX_BUDGET_NUM = 20

def is_admin():
    """Check if current user is admin"""
    return session.get('user_role') in ['admin', 'project_site_admin']

def require_admin(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not is_admin():
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('manual_entry'))
        return f(*args, **kwargs)
    return decorated_function

def get_user_project_site():
    """Get current user's project site"""
    # For global admins, use the selected project site from session (can be None for "All Sites")
    # For project site accounts, ALWAYS return their assigned project site (cannot be changed)
    if session.get('is_global_admin'):
        return session.get('project_site')  # Can be None for global admins
    else:
        # Project site admins: get from assigned_site (set at login, cannot be changed)
        # Fallback to project_site if assigned_site not set (backwards compatibility)
        return session.get('assigned_project_site') or session.get('project_site')

def get_assigned_project_site():
    """Get the permanently assigned project site for project site admins"""
    # This is the project site assigned at login - cannot be changed
    if session.get('is_global_admin'):
        return None  # Global admins don't have an assigned site
    return session.get('assigned_project_site') or session.get('project_site')

def filter_by_project_site(query):
    """Apply project site filter to query - ENFORCES strict separation"""
    # For project site admins: ALWAYS filter by their assigned site (non-negotiable)
    if not session.get('is_global_admin'):
        assigned_site = get_assigned_project_site()
        if assigned_site:
            # Project site admins can ONLY see their own site's data
            return query.filter_by(project_site=assigned_site)
        else:
            # If somehow no assigned site, return empty query for security
            return query.filter_by(project_site=None)  # This will return no results
    
    # For global admins: filter by selected project site if one is selected
    project_site = session.get('project_site')
    if project_site:
        return query.filter_by(project_site=project_site)
    # Global admin with no site selected = see all sites (return unfiltered query)
    return query

def can_edit():
    """Check if user can edit items"""
    return is_admin()

# Route: Manual Entry (Budget Builder)
def manual_entry():
    """Manual Entry tab"""
    # Get existing budgets filtered by project site
    budget_query = filter_by_project_site(Item.query) if get_user_project_site() else Item.query
    existing_budgets = [item.budget for item in budget_query.distinct(Item.budget).all() if item.budget]
    
    building_type = request.args.get('building_type', 'Flats')
    selected_section = request.args.get('section', CONSTRUCTION_SECTIONS[0] if CONSTRUCTION_SECTIONS else '')
    selected_budget = request.args.get('budget', '')
    
    # Generate budget options filtered by building type
    all_budgets = generate_budget_options(MAX_BUDGET_NUM, building_type, existing_budgets)
    
    # Handle form submission
    if request.method == 'POST' and can_edit():
        name = request.form.get('name', '').strip()
        qty = request.form.get('qty', '0')
        unit = request.form.get('unit', '').strip()
        unit_cost = request.form.get('unit_cost', '0')
        category = request.form.get('category', 'Materials')
        budget = request.form.get('budget', '').strip()
        section = request.form.get('section', '').strip()
        building_type_form = request.form.get('building_type', '').strip()
        
        # Debug: log received form data
        print(f"DEBUG - Received form data: budget={repr(budget)}, building_type={repr(building_type_form)}, section={repr(section)}")
        
        if not name:
            flash('Item name is required', 'error')
        elif not budget:
            flash('Budget label is required. Please select a budget from the "Project Context" section and click "Update Context", or ensure the budget dropdown is selected before adding the item.', 'error')
        elif not building_type_form:
            flash('Building type is required. Please select a building type from the "Project Context" section first.', 'error')
        elif not section:
            flash('Section is required. Please select a section from the "Project Context" section first.', 'error')
        else:
            try:
                qty = float(qty) if qty else 0.0
                unit_cost = float(unit_cost) if unit_cost else 0.0
                
                # Determine group
                grp = determine_group_from_category_and_budget(category, budget)
                
                item = Item(
                    name=name,
                    qty=qty,
                    unit=unit,
                    unit_cost=unit_cost,
                    category=category.lower(),
                    budget=budget,
                    section=section,
                    grp=grp,
                    building_type=building_type_form,
                    project_site=get_user_project_site()
                )
                db.session.add(item)
                db.session.commit()
                
                flash(f'Item "{name}" added successfully! This item will now appear in the Budget Summary tab.', 'success')
                
                # Note: No notification created for item added - only shows in Notifications tab, no popup
                
            except ValueError:
                flash('Invalid quantity or unit cost', 'error')
    
    # Get budget filter for view
    budget_filter = request.args.get('budget_filter', 'All')
    section_filter = request.args.get('section_filter', '')
    
    # Query items - filter by project site if one is selected
    query = filter_by_project_site(Item.query)
    
    if budget_filter and budget_filter != 'All':
        # Filter by budget (hierarchical matching)
        all_items = query.all()
        filtered_items = [item for item in all_items if match_budget_filter(item.budget, budget_filter)]
        query = query.filter(Item.id.in_([item.id for item in filtered_items]))
    
    if section_filter:
        query = query.filter_by(section=section_filter)
    
    items = query.order_by(Item.created_at.desc()).all()
    
    # Calculate totals
    total_amount = sum(item.amount for item in items)
    
    # Get unique sections for filter - filtered by project site
    sections_query = filter_by_project_site(Item.query) if get_user_project_site() else Item.query
    unique_sections = sorted(set([item.section for item in sections_query.distinct(Item.section).all() if item.section] + CONSTRUCTION_SECTIONS))
    
    return render_template('manual_entry.html',
                         building_type=building_type,
                         selected_section=selected_section,
                         selected_budget=selected_budget,
                         all_budgets=all_budgets,
                         budget_filter=budget_filter,
                         section_filter=section_filter,
                         items=items,
                         total_amount=total_amount,
                         unique_sections=unique_sections,
                         construction_sections=CONSTRUCTION_SECTIONS,
                         property_types=PROPERTY_TYPES,
                         can_edit=can_edit())

def download_budget_view():
    """Download budget view as CSV"""
    budget_filter = request.args.get('budget_filter', 'All')
    section_filter = request.args.get('section_filter', '')
    
    query = filter_by_project_site(Item.query)
    
    if budget_filter and budget_filter != 'All':
        all_items = query.all()
        filtered_items = [item for item in all_items if match_budget_filter(item.budget, budget_filter)]
        query = query.filter(Item.id.in_([item.id for item in filtered_items]))
    
    if section_filter:
        query = query.filter_by(section=section_filter)
    
    items = query.all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['budget', 'section', 'grp', 'building_type', 'name', 'qty', 'unit', 'unit_cost', 'Amount'])
    
    for item in items:
        writer.writerow([
            item.budget or '',
            item.section or '',
            item.grp or '',
            item.building_type or '',
            item.name,
            item.qty,
            item.unit or '',
            item.unit_cost or 0,
            item.amount
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name='budget_view.csv'
    )

# Route: Inventory
def inventory():
    """Inventory tab"""
    budget_filter = request.args.get('budget_filter', 'All')
    section_filter = request.args.get('section_filter', 'All')
    building_type_filter = request.args.get('building_type_filter', 'All')
    page = int(request.args.get('page', 1))
    per_page = 50
    
    # Start with base query - apply project site filter first
    base_query = filter_by_project_site(Item.query)
    
    # Get total items before filtering (for statistics)
    total_items_before_filtering = base_query.count()
    
    # Apply filters sequentially
    query = base_query
    
    # Budget filter (hierarchical matching)
    if budget_filter and budget_filter != 'All':
        all_items = query.all()
        filtered_items = [item for item in all_items if match_budget_filter(item.budget, budget_filter)]
        if filtered_items:
            query = query.filter(Item.id.in_([item.id for item in filtered_items]))
        else:
            # No items match, return empty query
            query = query.filter(Item.id.in_([]))
    
    # Section filter
    if section_filter and section_filter != 'All':
        query = query.filter_by(section=section_filter)
    
    # Building type filter
    if building_type_filter and building_type_filter != 'All':
        query = query.filter_by(building_type=building_type_filter)
    
    total_items = query.count()
    items = query.order_by(Item.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistics - use the base query (before applying filters)
    all_items_list = base_query.all()
    
    total_value = sum(item.amount for item in all_items_list)
    materials_count = len([i for i in all_items_list if i.category == 'materials'])
    labour_count = len([i for i in all_items_list if i.category == 'labour'])
    
    # Get unique values for filters - filtered by project site
    sections_query = filter_by_project_site(Item.query) if get_user_project_site() else Item.query
    unique_sections = sorted(set([item.section for item in sections_query.distinct(Item.section).all() if item.section] + CONSTRUCTION_SECTIONS))
    budgets_query = filter_by_project_site(Item.query) if get_user_project_site() else Item.query
    existing_budgets = [item.budget for item in budgets_query.distinct(Item.budget).all() if item.budget]
    all_budgets = ['All'] + generate_budget_options(MAX_BUDGET_NUM, None, existing_budgets)
    
    return render_template('inventory.html',
                         items=items,
                         total_items=total_items,
                         total_items_before_filtering=total_items_before_filtering,
                         total_value=total_value,
                         materials_count=materials_count,
                         labour_count=labour_count,
                         budget_filter=budget_filter,
                         section_filter=section_filter,
                         building_type_filter=building_type_filter,
                         unique_sections=unique_sections,
                         all_budgets=all_budgets,
                         property_types=PROPERTY_TYPES,
                         can_edit=can_edit())

def edit_item(item_id):
    """Edit item (AJAX endpoint)"""
    if not can_edit():
        return jsonify({'error': 'Permission denied'}), 403
    
    # Use get() instead of get_or_404 to handle missing items gracefully for AJAX
    item = Item.query.get(item_id)
    if not item:
        return jsonify({'error': f'Item with ID {item_id} not found'}), 404
    
    # Check project site permissions
    project_site = get_user_project_site()
    if project_site and item.project_site != project_site:
        return jsonify({'error': 'Permission denied: Item belongs to different project site'}), 403
    
    if request.method == 'POST':
        try:
            new_qty = float(request.form.get('new_qty', item.qty))
            new_unit_cost = float(request.form.get('new_unit_cost', item.unit_cost or 0))
            
            old_amount = item.amount
            item.qty = new_qty
            item.unit_cost = new_unit_cost
            db.session.commit()
            
            new_amount = item.amount
            change = new_amount - old_amount
            
            # Return JSON for AJAX calls
            return jsonify({
                'success': True,
                'message': f'Item "{item.name}" updated successfully!',
                'old_amount': old_amount,
                'new_amount': new_amount,
                'change': change
            })
        except ValueError:
            return jsonify({'error': 'Invalid values provided'}), 400
    
    # GET request - redirect to inventory
    return redirect(url_for('inventory'))

def delete_item(item_id):
    """Delete item (supports both GET redirects and POST AJAX)"""
    # Always return JSON for POST requests to avoid HTML error pages
    is_post = request.method == 'POST'
    
    if not can_edit():
        if is_post:
            return jsonify({'error': 'Permission denied'}), 403
        flash('Permission denied', 'error')
        return redirect(url_for('inventory'))
    
    try:
        # Use get() instead of get_or_404 to handle missing items gracefully
        item = Item.query.get(item_id)
        if not item:
            if is_post:
                return jsonify({'error': f'Item with ID {item_id} not found'}), 404
            flash(f'Item with ID {item_id} not found', 'error')
            return redirect(url_for('inventory'))
        
        item_name = item.name
        
        # Security check: Ensure item belongs to current project site
        # For project site admins, use assigned_project_site (strict check)
        # For global admins, use selected project site
        if not session.get('is_global_admin'):
            assigned_site = get_assigned_project_site()
            if item.project_site != assigned_site:
                if is_post:
                    return jsonify({'error': 'Permission denied: Item belongs to different project site'}), 403
                flash('Permission denied: Item belongs to different project site', 'error')
                return redirect(url_for('inventory'))
        else:
            project_site = get_user_project_site()
            if project_site and item.project_site != project_site:
                if is_post:
                    return jsonify({'error': 'Permission denied: Item belongs to different project site'}), 403
                flash('Permission denied: Item belongs to different project site', 'error')
                return redirect(url_for('inventory'))
        
        db.session.delete(item)
        db.session.commit()
        
        if is_post:
            return jsonify({'success': True, 'message': f'Item "{item_name}" deleted successfully!'})
        
        flash(f'Item "{item_name}" deleted successfully!', 'success')
        return redirect(url_for('inventory'))
    except Exception as e:
        db.session.rollback()
        if is_post:
            return jsonify({'error': f'Failed to delete item: {str(e)}'}), 500
        flash(f'Error deleting item: {str(e)}', 'error')
        return redirect(url_for('inventory'))

def delete_all_inventory():
    """Delete all inventory and optionally requests"""
    if not can_edit():
        flash('Permission denied', 'error')
        return redirect(url_for('inventory'))
    
    if request.method == 'POST':
        clear_requests = request.form.get('clear_requests') == 'on'
        
        # STRICT SEPARATION: Project site admins can ONLY delete their own site's data
        if not session.get('is_global_admin'):
            assigned_site = get_assigned_project_site()
            if assigned_site:
                Item.query.filter_by(project_site=assigned_site).delete()
                if clear_requests:
                    Request.query.filter_by(project_site=assigned_site).delete()
            else:
                flash('Permission denied: No assigned project site', 'error')
                return redirect(url_for('inventory'))
        else:
            # Global admins: delete based on selected project site (if any)
            project_site = get_user_project_site()
            if project_site:
                Item.query.filter_by(project_site=project_site).delete()
                if clear_requests:
                    Request.query.filter_by(project_site=project_site).delete()
            else:
                # If no project site selected and user is global admin, delete all
                Item.query.delete()
                if clear_requests:
                    Request.query.delete()
        db.session.commit()
        
        flash('All inventory items deleted successfully!', 'success')
    
    return redirect(url_for('inventory'))

# Route: Make Request
def make_request():
    """Make Request tab"""
    # Get items for current project site
    query = filter_by_project_site(Item.query)
    items = query.order_by(Item.name).all()
    
    if request.method == 'POST':
        item_id = request.form.get('item_id')
        qty = request.form.get('qty', '1.0')
        current_rate = request.form.get('current_rate', '')
        note = request.form.get('note', '').strip()
        section = request.form.get('section', '')
        building_type = request.form.get('building_type', '')
        budget = request.form.get('budget', '')
        
        # Validation
        if not item_id:
            flash('Please select an item', 'error')
        elif not note:
            flash('Note is required', 'error')
        elif not section:
            flash('Section is required', 'error')
        elif not building_type:
            flash('Building type is required', 'error')
        elif not budget:
            flash('Budget is required', 'error')
        else:
            try:
                item = Item.query.get(int(item_id))
                if not item:
                    flash('Selected item not found', 'error')
                else:
                    qty = float(qty) if qty else 1.0
                    current_rate = float(current_rate) if current_rate else (item.unit_cost or 0)
                    
                    req = Request(
                        item_id=item.id,
                        qty=qty,
                        requested_by=session.get('user_name', 'Unknown'),
                        note=note,
                        section=section,
                        building_type=building_type,
                        budget=budget,
                        current_price=current_rate,
                        project_site=get_user_project_site()
                    )
                    db.session.add(req)
                    db.session.commit()
                    
                    # Create notifications
                    # Note: No notification to requester on submit - they can see it in Review & History tab
                    
                    # Notify global admins ONLY (this will trigger popup for admins)
                    # Only notify if requester is from a project site (not global admin)
                    if not session.get('is_global_admin'):
                        notif_admin = Notification(
                            notification_type='request',
                            title='New Request',
                            message=f'New request for {item.name} from {req.requested_by} ({get_user_project_site() or "Unknown Site"})',
                            user_id=None,  # None means notify all global admins
                            request_id=req.id
                        )
                        db.session.add(notif_admin)
                    db.session.commit()
                    
                    flash(f'Request submitted successfully! Request ID: {req.id}', 'success')
                    return redirect(url_for('make_request'))
            except ValueError:
                flash('Invalid quantity or rate', 'error')
    
    # Get existing budgets filtered by project site
    budgets_query = filter_by_project_site(Item.query) if get_user_project_site() else Item.query
    existing_budgets = [item.budget for item in budgets_query.distinct(Item.budget).all() if item.budget]
    all_budgets = generate_budget_options(MAX_BUDGET_NUM, None, existing_budgets)
    
    return render_template('make_request.html',
                         items=items,
                         all_budgets=all_budgets,
                         construction_sections=['materials', 'labour'],
                         property_types=PROPERTY_TYPES)

# Route: Review & History
def review_history():
    """Review & History tab"""
    status_filter = request.args.get('status_filter', 'Pending')
    active_tab = request.args.get('tab', 'approved')  # approved, rejected, deleted
    
    # Base query - use filter_by_project_site for strict separation
    base_query = filter_by_project_site(Request.query)
    project_site = get_user_project_site()
    
    if not is_admin():
        # Project site accounts only see their own requests
        base_query = base_query.filter_by(requested_by=session.get('user_name', ''))
    
    # Get all requests for tab filtering
    all_requests_query = base_query
    
    # Get requests for each tab
    approved_requests = all_requests_query.filter_by(status='Approved').order_by(Request.created_at.desc()).all()
    rejected_requests = all_requests_query.filter_by(status='Rejected').order_by(Request.created_at.desc()).all()
    
    # For status filter dropdown
    if status_filter and status_filter != 'All':
        filtered_query = base_query.filter_by(status=status_filter)
    else:
        filtered_query = base_query
    
    requests = filtered_query.order_by(Request.created_at.desc()).paginate(page=1, per_page=20, error_out=False)
    
    # Statistics - filtered by project site (strict separation)
    stats_query = filter_by_project_site(Request.query)
    if not is_admin():
        stats_query = stats_query.filter_by(requested_by=session.get('user_name', ''))
    
    all_requests = stats_query.all()
    pending_count = len([r for r in all_requests if r.status == 'Pending'])
    approved_count = len([r for r in all_requests if r.status == 'Approved'])
    rejected_count = len([r for r in all_requests if r.status == 'Rejected'])
    
    return render_template('review_history.html',
                         requests=requests,
                         status_filter=status_filter,
                         active_tab=active_tab,
                         approved_requests=approved_requests,
                         rejected_requests=rejected_requests,
                         pending_count=pending_count,
                         approved_count=approved_count,
                         rejected_count=rejected_count,
                         total_count=len(all_requests),
                         is_admin=is_admin(),
                         can_delete_own=not is_admin())

def approve_request(request_id):
    """Approve a request"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('review_history'))
    
    req = Request.query.get_or_404(request_id)
    
    # Security check: Project site admins can only approve requests from their own site
    if not session.get('is_global_admin'):
        assigned_site = get_assigned_project_site()
        if req.project_site != assigned_site:
            flash('Permission denied. You can only approve requests from your assigned project site.', 'error')
            return redirect(url_for('review_history'))
    req.status = 'Approved'
    req.approved_by = session.get('user_name', 'Unknown')
    req.updated_at = datetime.utcnow()
    
    # Create Actual record from approved request
    # Calculate actual cost: quantity * current price (or fall back to item unit cost)
    current_price = float(req.current_price) if req.current_price else (float(req.item.unit_cost) if req.item.unit_cost else 0)
    actual_cost = float(req.qty) * current_price
    
    # Check if Actual record already exists for this request (to avoid duplicates)
    existing_actual = Actual.query.filter_by(item_id=req.item_id).filter_by(notes=f'Request #{req.id}').first()
    
    if not existing_actual:
        actual = Actual(
            item_id=req.item_id,
            actual_qty=req.qty,
            actual_cost=actual_cost,
            actual_date=req.created_at.strftime('%Y-%m-%d'),
            recorded_by=req.approved_by,
            notes=f'Request #{req.id}',
            project_site=req.project_site
        )
        db.session.add(actual)
    
    db.session.commit()
    
    # Find the requester's user_id by matching requested_by name with access codes
    # This notification will trigger popup for project site accounts
    requester_user_id = None
    if req.project_site:
        # Try to find the access code for the project site requester
        site_code = AccessCode.query.filter_by(
            code_type='project_site',
            project_site=req.project_site
        ).first()
        if site_code:
            requester_user_id = site_code.id
    
    # Create notification for requester (only if requester is a project site account)
    if requester_user_id:
        notif = Notification(
            notification_type='approval',
            title='Request Approved',
            message=f'Your request for {req.item.name} has been approved by {req.approved_by}.',
            user_id=requester_user_id,
            request_id=req.id
        )
        db.session.add(notif)
        db.session.commit()
    
    flash('Request approved successfully! It has been added to Actuals.', 'success')
    return redirect(url_for('review_history'))

def reject_request(request_id):
    """Reject a request"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('review_history'))
    
    req = Request.query.get_or_404(request_id)
    
    # Security check: Project site admins can only reject requests from their own site
    if not session.get('is_global_admin'):
        assigned_site = get_assigned_project_site()
        if req.project_site != assigned_site:
            flash('Permission denied. You can only reject requests from your assigned project site.', 'error')
            return redirect(url_for('review_history'))
    req.status = 'Rejected'
    req.approved_by = session.get('user_name', 'Unknown')
    req.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Find the requester's user_id by matching project site
    # This notification will trigger popup for project site accounts
    requester_user_id = None
    if req.project_site:
        # Try to find the access code for the project site requester
        site_code = AccessCode.query.filter_by(
            code_type='project_site',
            project_site=req.project_site
        ).first()
        if site_code:
            requester_user_id = site_code.id
    
    # Create notification for requester (only if requester is a project site account)
    if requester_user_id:
        notif = Notification(
            notification_type='rejection',
            title='Request Rejected',
            message=f'Your request for {req.item.name} has been rejected by {req.approved_by}.',
            user_id=requester_user_id,
            request_id=req.id
        )
        db.session.add(notif)
        db.session.commit()
    
    flash('Request rejected', 'info')
    return redirect(url_for('review_history'))

def delete_request(request_id):
    """Delete a request and its associated notifications"""
    req = Request.query.get_or_404(request_id)
    
    # Check permissions with strict project site separation
    is_global_admin = session.get('is_global_admin', False)
    user_is_owner = req.requested_by == session.get('user_name')
    can_delete_by_status = req.status in ['Approved', 'Rejected']
    
    if is_global_admin:
        can_delete = True  # Global admins can delete any request
    elif not session.get('is_global_admin'):
        # Project site admins: can only delete requests from their own site
        assigned_site = get_assigned_project_site()
        can_delete = (req.project_site == assigned_site) and (is_admin() or (user_is_owner and can_delete_by_status))
    else:
        # Regular users can only delete their own requests
        can_delete = user_is_owner and can_delete_by_status
    
    if not can_delete:
        flash('Permission denied', 'error')
        return redirect(url_for('review_history'))
    
    # Delete all notifications associated with this request
    # This ensures notifications are removed from both admin and project site accounts
    related_notifications = Notification.query.filter_by(request_id=request_id).all()
    for notif in related_notifications:
        db.session.delete(notif)
    
    # Delete the request
    db.session.delete(req)
    db.session.commit()
    
    flash('Request deleted successfully! Associated notifications have been removed.', 'success')
    return redirect(url_for('review_history'))

def approve_reject_by_id():
    """Approve or reject a request by ID (from form)"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('review_history'))
    
    request_id = request.form.get('request_id')
    action = request.form.get('action')
    approved_by = request.form.get('approved_by') or session.get('user_name', 'Unknown')
    
    if not request_id:
        flash('Request ID is required', 'error')
        return redirect(url_for('review_history'))
    
    try:
        req = Request.query.get_or_404(int(request_id))
        
        # Security check: Project site admins can only approve/reject requests from their own site
        if not session.get('is_global_admin'):
            assigned_site = get_assigned_project_site()
            if req.project_site != assigned_site:
                flash('Permission denied. You can only approve/reject requests from your assigned project site.', 'error')
                return redirect(url_for('review_history'))
        
        if action == 'approve':
            req.status = 'Approved'
            req.approved_by = approved_by
            req.updated_at = datetime.utcnow()
            
            # Create Actual record from approved request
            # Calculate actual cost: quantity * current price (or fall back to item unit cost)
            current_price = float(req.current_price) if req.current_price else (float(req.item.unit_cost) if req.item.unit_cost else 0)
            actual_cost = float(req.qty) * current_price
            
            # Check if Actual record already exists for this request (to avoid duplicates)
            existing_actual = Actual.query.filter_by(item_id=req.item_id).filter_by(notes=f'Request #{req.id}').first()
            
            if not existing_actual:
                actual = Actual(
                    item_id=req.item_id,
                    actual_qty=req.qty,
                    actual_cost=actual_cost,
                    actual_date=req.created_at.strftime('%Y-%m-%d'),
                    recorded_by=approved_by,
                    notes=f'Request #{req.id}',
                    project_site=req.project_site
                )
                db.session.add(actual)
            
            db.session.commit()
            
            # Create notification for requester
            requester_user_id = None
            if req.project_site:
                site_code = AccessCode.query.filter_by(
                    code_type='project_site',
                    project_site=req.project_site
                ).first()
                if site_code:
                    requester_user_id = site_code.id
            
            if requester_user_id:
                notif = Notification(
                    notification_type='approval',
                    title='Request Approved',
                    message=f'Your request for {req.item.name} has been approved by {approved_by}.',
                    user_id=requester_user_id,
                    request_id=req.id
                )
                db.session.add(notif)
                db.session.commit()
            
            flash(f'Request #{request_id} approved successfully! It has been added to Actuals.', 'success')
        elif action == 'reject':
            req.status = 'Rejected'
            req.approved_by = approved_by
            req.updated_at = datetime.utcnow()
            db.session.commit()
            
            # Create notification for requester
            requester_user_id = None
            if req.project_site:
                site_code = AccessCode.query.filter_by(
                    code_type='project_site',
                    project_site=req.project_site
                ).first()
                if site_code:
                    requester_user_id = site_code.id
            
            if requester_user_id:
                notif = Notification(
                    notification_type='rejection',
                    title='Request Rejected',
                    message=f'Your request for {req.item.name} has been rejected by {approved_by}.',
                    user_id=requester_user_id,
                    request_id=req.id
                )
                db.session.add(notif)
                db.session.commit()
            
            flash(f'Request #{request_id} rejected', 'info')
        else:
            flash('Invalid action', 'error')
    except ValueError:
        flash('Invalid request ID', 'error')
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
    
    return redirect(url_for('review_history'))

# Route: Budget Summary
def budget_summary():
    """Budget Summary tab"""
    # Filter items by project site if one is selected
    query = filter_by_project_site(Item.query)
    items = query.all()
    
    # Statistics
    total_items = len(items)
    total_amount = sum(item.amount for item in items)
    unique_budgets = len(set([item.budget for item in items if item.budget]))
    unique_building_types = len(set([item.building_type for item in items if item.building_type]))
    
    # Recent items
    recent_items = sorted(items, key=lambda x: x.created_at, reverse=True)[:10]
    
    # Summary by budget and building type
    summary_data = {}
    for item in items:
        if item.budget and item.building_type:
            # Extract budget number
            try:
                budget_num = item.budget.split(' ')[1].split(' ')[0]  # "Budget 1 - Flats(...)"
            except:
                budget_num = 'Unknown'
            
            if budget_num not in summary_data:
                summary_data[budget_num] = {}
            
            building_type = item.building_type
            if building_type not in summary_data[budget_num]:
                summary_data[budget_num][building_type] = 0.0
            
            summary_data[budget_num][building_type] += item.amount
    
    # Get selected budget for Manual Budget Summary view
    selected_budget_num = request.args.get('budget', '1')
    
    # Calculate total for selected budget
    selected_budget_total = 0.0
    selected_budget_breakdown = {}
    if selected_budget_num in summary_data:
        selected_budget_breakdown = summary_data[selected_budget_num]
        selected_budget_total = sum(selected_budget_breakdown.values())
    
    # Get building type configurations
    project_site = get_user_project_site()
    from models import BuildingTypeConfig
    building_configs = {}
    for building_type in PROPERTY_TYPES:
        config = BuildingTypeConfig.query.filter_by(
            building_type=building_type,
            project_site=project_site
        ).first()
        if config:
            building_configs[building_type] = config
        else:
            # Default values - create a simple dict-like object
            class DefaultConfig:
                def __init__(self):
                    self.blocks = 0
                    self.units_per_block = 0
                    self.notes = ''
            building_configs[building_type] = DefaultConfig()
    
    # Calculate amounts per building type for selected budget
    # Get the amount per block from database (first block's total)
    amount_per_block_data = {}
    for building_type in PROPERTY_TYPES:
        building_items = [item for item in items if item.building_type == building_type and 
                         item.budget and f'Budget {selected_budget_num}' in item.budget]
        if building_items:
            total_amount = sum(item.amount for item in building_items)
            amount_per_block_data[building_type] = total_amount
    
    if request.args.get('download') == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Budget', 'Flats', 'Terraces', 'Semi-detached', 'Fully-detached', 'Total'])
        
        for budget_num in sorted(summary_data.keys(), key=lambda x: int(x) if x.isdigit() else 999):
            row = [f'Budget {budget_num}']
            totals = summary_data[budget_num]
            flats = totals.get('Flats', 0)
            terraces = totals.get('Terraces', 0)
            semi = totals.get('Semi-detached', 0)
            fully = totals.get('Fully-detached', 0)
            total = flats + terraces + semi + fully
            row.extend([flats, terraces, semi, fully, total])
            writer.writerow(row)
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name='budget_summary.csv'
        )
    
    return render_template('budget_summary.html',
                         total_items=total_items,
                         total_amount=total_amount,
                         unique_budgets=unique_budgets,
                         unique_building_types=unique_building_types,
                         recent_items=recent_items,
                         summary_data=summary_data,
                         property_types=PROPERTY_TYPES,
                         max_budget_num=MAX_BUDGET_NUM,
                         items=items,
                         selected_budget_num=selected_budget_num,
                         selected_budget_total=selected_budget_total,
                         selected_budget_breakdown=selected_budget_breakdown,
                         building_configs=building_configs,
                         amount_per_block_data=amount_per_block_data)

# Route: Save Building Type Configuration
def save_building_config():
    """Save building type configuration (blocks, units per block, notes)"""
    if request.method == 'POST':
        building_type = request.form.get('building_type')
        blocks = int(request.form.get('blocks', 0))
        units_per_block = int(request.form.get('units_per_block', 0))
        notes = request.form.get('notes', '')
        project_site = get_user_project_site()
        
        if not building_type:
            flash('Building type is required', 'error')
            return redirect(url_for('budget_summary'))
        
        # Find existing config or create new
        config = BuildingTypeConfig.query.filter_by(
            building_type=building_type,
            project_site=project_site
        ).first()
        
        if config:
            config.blocks = blocks
            config.units_per_block = units_per_block
            config.notes = notes
            config.updated_at = datetime.utcnow()
        else:
            config = BuildingTypeConfig(
                building_type=building_type,
                blocks=blocks,
                units_per_block=units_per_block,
                notes=notes,
                project_site=project_site
            )
            db.session.add(config)
        
        db.session.commit()
        flash(f'{building_type} configuration saved successfully!', 'success')
    
    return redirect(url_for('budget_summary'))

# Route: Actuals
def actuals():
    """Actuals tab"""
    selected_budget = request.args.get('budget', '')
    
    # Generate budget options (Budget 1-20 for each building type)
    budget_options = []
    for budget_num in range(1, MAX_BUDGET_NUM + 1):
        for building_type in PROPERTY_TYPES:
            budget_options.append(f"Budget {budget_num} - {building_type}")
    
    # Sort numerically by budget number, not alphabetically
    def extract_budget_number(budget_str):
        """Extract budget number from string like 'Budget 1 - Flats'"""
        try:
            parts = budget_str.split("Budget ", 1)
            if len(parts) > 1:
                num_str = parts[1].split(" -")[0].strip()
                return int(num_str)
        except (ValueError, IndexError):
            pass
        return 999
    
    budget_options = sorted(budget_options, key=lambda x: (extract_budget_number(x), x))
    
    if not selected_budget:
        return render_template('actuals.html',
                             selected_budget='',
                             budget_options=budget_options,
                             planned_data=None,
                             actual_data=None,
                             can_edit=can_edit())
    
    # Parse selected budget
    parts = selected_budget.split(' - ')
    if len(parts) != 2:
        flash('Invalid budget selection', 'error')
        return redirect(url_for('actuals'))
    
    budget_num = parts[0].replace('Budget ', '').strip()
    building_type = parts[1].strip()
    
    # Get planned budget items - filtered by project site
    query = filter_by_project_site(Item.query)
    
    # Filter items that match this budget pattern
    # Items can have budget like "Budget 1 - Flats(General Materials)"
    # We need to match items where:
    # 1. Budget starts with "Budget {budget_num} - {building_type}"
    # 2. Building type matches exactly
    all_items = query.all()
    planned_items = []
    budget_pattern = f"Budget {budget_num} - {building_type}"
    
    for item in all_items:
        # Match budget pattern (can include subgroup like "(General Materials)")
        budget_matches = False
        if item.budget:
            # Check if budget starts with the pattern we're looking for
            # e.g., "Budget 1 - Flats" should match "Budget 1 - Flats(General Materials)"
            if item.budget.startswith(budget_pattern):
                budget_matches = True
        
        # Building type must match exactly (case-insensitive)
        building_matches = False
        if item.building_type:
            building_matches = item.building_type.strip().lower() == building_type.strip().lower()
        elif building_type and not item.building_type:
            # If building_type is required but item doesn't have one, don't match
            building_matches = False
        
        if budget_matches and building_matches:
            planned_items.append(item)
    
    # Group by category (grp)
    planned_by_category = {}
    for item in planned_items:
        grp = item.grp or 'Materials'
        if grp not in planned_by_category:
            planned_by_category[grp] = []
        planned_by_category[grp].append(item)
    
    # Get actuals - filtered by project site
    actual_query = Actual.query
    project_site = get_user_project_site()
    if project_site:
        actual_query = actual_query.filter_by(project_site=project_site)
    
    # Build actual_by_category with ALL planned items (show 0 if no actuals yet)
    actual_by_category = {}
    for item in planned_items:
        grp = item.grp or 'Materials'
        if grp not in actual_by_category:
            actual_by_category[grp] = []
        
        # Get actuals for this item
        item_actuals = actual_query.filter_by(item_id=item.id).all()
        
        if item_actuals:
            # Sum up all actuals for this item
            total_qty = sum(float(a.actual_qty) for a in item_actuals)
            total_cost = sum(float(a.actual_cost) for a in item_actuals)
        else:
            # No approved requests yet - show 0
            total_qty = 0.0
            total_cost = 0.0
        
        # Always add the item to actuals (even if 0, until approved)
        actual_by_category[grp].append({
            'item': item,
            'qty': total_qty,
            'cost': total_cost
        })
    
    return render_template('actuals.html',
                         selected_budget=selected_budget,
                         budget_options=budget_options,
                         planned_data=planned_by_category,
                         actual_data=actual_by_category,
                         can_edit=can_edit())

# Route: Admin Settings
def admin_settings():
    """Admin Settings tab (Global Admin only)"""
    if not session.get('is_global_admin'):
        flash('Access denied. Global admin privileges required.', 'error')
        return redirect(url_for('manual_entry'))
    
    # Statistics
    project_sites_count = ProjectSite.query.count()
    total_items = Item.query.count()
    total_requests = Request.query.count()
    
    # Today's access logs
    today = datetime.utcnow().date()
    today_logs = AccessLog.query.filter(
        db.func.date(AccessLog.created_at) == today
    ).count()
    
    # Notification statistics
    unread_admin_notifications = Notification.query.filter_by(
        user_id=None,
        is_read=False
    ).count()
    total_admin_notifications = Notification.query.filter_by(
        user_id=None
    ).count()
    recent_notifications = Notification.query.filter_by(
        user_id=None
    ).order_by(Notification.created_at.desc()).limit(10).all()
    
    # Get global admin code
    admin_code_obj = AccessCode.query.filter_by(
        code_type='global_admin',
        project_site=None
    ).first()
    current_admin_code = admin_code_obj.display_code if admin_code_obj and admin_code_obj.display_code else None
    
    # Get project sites with their access codes
    project_sites = ProjectSite.query.all()
    project_sites_with_codes = []
    for site in project_sites:
        access_code = AccessCode.query.filter_by(
            code_type='project_site',
            project_site=site.name
        ).first()
        site_data = {
            'site': site,
            'access_code': access_code.display_code if access_code and access_code.display_code else None,
            'has_access_code': access_code is not None,
            'access_code_id': access_code.id if access_code else None
        }
        project_sites_with_codes.append(site_data)
    
    return render_template('admin_settings.html',
                         project_sites_count=project_sites_count,
                         total_items=total_items,
                         total_requests=total_requests,
                         today_access=today_logs,
                         project_sites=ProjectSite.query.all(),
                         project_sites_with_codes=project_sites_with_codes,
                         current_project_site=get_user_project_site(),
                         current_admin_code=current_admin_code,
                         unread_admin_notifications=unread_admin_notifications,
                         total_admin_notifications=total_admin_notifications,
                         recent_notifications=recent_notifications)

def update_global_admin_code():
    """Update global admin access code"""
    if not is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    
    if request.method == 'POST':
        new_code = request.form.get('new_code', '').strip()
        if not new_code:
            return jsonify({'error': 'Code is required'}), 400
        
        admin_code = AccessCode.query.filter_by(code_type='global_admin', project_site=None).first()
        if admin_code:
            admin_code.code_hash = generate_password_hash(new_code)
            admin_code.display_code = new_code  # Store plaintext for admin display
            admin_code.updated_at = datetime.utcnow()
        else:
            admin_code = AccessCode(
                code_type='global_admin',
                project_site=None,
                code_hash=generate_password_hash(new_code),
                display_code=new_code  # Store plaintext for admin display
            )
            db.session.add(admin_code)
        
        db.session.commit()
        return jsonify({'success': True})
    
    return redirect(url_for('admin_settings'))

def update_project_site_code():
    """Update project site access code (single code per site)"""
    if not is_admin():
        return jsonify({'error': 'Permission denied'}), 403
    
    if request.method == 'POST':
        project_site = request.form.get('project_site', '').strip()
        new_code = request.form.get('new_code', '').strip()
        
        if not project_site or not new_code:
            return jsonify({'error': 'Project site and code are required'}), 400
        
        access_code = AccessCode.query.filter_by(
            code_type='project_site',
            project_site=project_site
        ).first()
        
        if access_code:
            access_code.code_hash = generate_password_hash(new_code)
            access_code.display_code = new_code  # Store plaintext for admin display
            access_code.updated_at = datetime.utcnow()
        else:
            access_code = AccessCode(
                code_type='project_site',
                project_site=project_site,
                code_hash=generate_password_hash(new_code),
                display_code=new_code  # Store plaintext for admin display
            )
            db.session.add(access_code)
        
        db.session.commit()
        flash(f'Access code for "{project_site}" updated successfully!', 'success')
        return jsonify({'success': True})
    
    return redirect(url_for('admin_settings'))

def add_project_site():
    """Add new project site"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('admin_settings'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        access_code = request.form.get('access_code', '').strip()
        
        if not name:
            flash('Project site name is required', 'error')
        elif ProjectSite.query.filter_by(name=name).first():
            flash('Project site with this name already exists', 'error')
        else:
            site = ProjectSite(name=name, description=description)
            db.session.add(site)
            db.session.commit()
            
            # Create access code if provided
            if access_code:
                code = AccessCode(
                    code_type='project_site',
                    project_site=name,
                    code_hash=generate_password_hash(access_code),
                    display_code=access_code  # Store plaintext for admin display
                )
                db.session.add(code)
                db.session.commit()
                flash(f'Project site "{name}" added successfully with access code!', 'success')
            else:
                flash(f'Project site "{name}" added successfully! You can now set the access code.', 'success')
    
    return redirect(url_for('admin_settings'))

def edit_project_site():
    """Edit project site"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('admin_settings'))
    
    if request.method == 'POST':
        site_id = request.form.get('site_id')
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        if not site_id:
            flash('Project site ID is required', 'error')
            return redirect(url_for('admin_settings'))
        
        site = ProjectSite.query.get_or_404(site_id)
        old_name = site.name
        
        if not name:
            flash('Project site name is required', 'error')
        elif name != old_name and ProjectSite.query.filter_by(name=name).first():
            flash('Project site with this name already exists', 'error')
        else:
            site.name = name
            site.description = description
            
            # Update access code project_site reference if name changed
            if name != old_name:
                access_code = AccessCode.query.filter_by(
                    code_type='project_site',
                    project_site=old_name
                ).first()
                if access_code:
                    access_code.project_site = name
            
            db.session.commit()
            flash(f'Project site updated successfully!', 'success')
    
    return redirect(url_for('admin_settings'))

def delete_project_site():
    """Delete project site"""
    if not session.get('is_global_admin'):
        flash('Permission denied. Only global admins can delete project sites.', 'error')
        return redirect(url_for('admin_settings'))
    
    site_id = request.args.get('site_id') or request.form.get('site_id')
    if not site_id:
        flash('Project site ID is required', 'error')
        return redirect(url_for('admin_settings'))
    
    site = ProjectSite.query.get_or_404(site_id)
    site_name = site.name
    
    # Delete associated access code
    access_code = AccessCode.query.filter_by(
        code_type='project_site',
        project_site=site_name
    ).first()
    if access_code:
        db.session.delete(access_code)
    
    # Delete project site
    db.session.delete(site)
    db.session.commit()
    
    flash(f'Project site "{site_name}" and its access code deleted successfully!', 'success')
    return redirect(url_for('admin_settings'))

def switch_project_site():
    """Switch current project site (for global admins ONLY)"""
    # STRICT CHECK: Only global admins can switch project sites
    if not session.get('is_global_admin'):
        flash('Permission denied. Only global administrators can switch project sites.', 'error')
        return redirect(url_for('manual_entry'))
    
    # Double-check: Ensure project site admins cannot bypass this
    if session.get('user_role') == 'project_site_admin':
        flash('Permission denied. Project site accounts are restricted to their assigned site.', 'error')
        return redirect(url_for('manual_entry'))
    
    if request.method == 'POST':
        project_site = request.form.get('project_site', '').strip()
        # For global admins, project_site can be None (all sites) or a specific site
        session['project_site'] = project_site if project_site else None
        # assigned_project_site should NOT exist for global admins
        if 'assigned_project_site' in session:
            session.pop('assigned_project_site', None)
        flash(f'Switched to project site: {project_site if project_site else "All Sites"}', 'success')
        
        # Redirect back to referrer if available, otherwise to manual entry
        referrer = request.headers.get('Referer')
        if referrer:
            from urllib.parse import urlparse
            parsed = urlparse(referrer)
            # Only redirect to safe internal paths
            if parsed.path and parsed.path.startswith('/') and parsed.path != '/switch_project_site':
                return redirect(parsed.path)
    
    # Default redirect to manual entry
    return redirect(url_for('manual_entry'))

def access_logs():
    """View access logs"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('admin_settings'))
    
    role_filter = request.args.get('role_filter', 'All')
    days = int(request.args.get('days', 7))
    page = int(request.args.get('page', 1))
    per_page = 20
    
    query = AccessLog.query
    
    if role_filter and role_filter != 'All':
        query = query.filter_by(role=role_filter)
    
    # Filter by date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    query = query.filter(AccessLog.created_at >= cutoff_date)
    
    logs = query.order_by(AccessLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    # Statistics
    all_logs = AccessLog.query.filter(AccessLog.created_at >= cutoff_date).all()
    total_logs = len(all_logs)
    successful = len([l for l in all_logs if l.status == 'Success'])
    failed = len([l for l in all_logs if l.status == 'Failed'])
    unique_users = len(set([l.user for l in all_logs if l.user]))
    
    today = datetime.utcnow().date()
    today_logs = AccessLog.query.filter(
        db.func.date(AccessLog.created_at) == today
    ).count()
    
    return render_template('access_logs.html',
                         logs=logs,
                         role_filter=role_filter,
                         days=days,
                         total_logs=total_logs,
                         today_access=today_logs,
                         successful=successful,
                         failed=failed,
                         unique_users=unique_users,
                         total_count=total_logs)

def clear_access_logs():
    """Clear all access logs"""
    if not is_admin():
        flash('Permission denied', 'error')
        return redirect(url_for('admin_settings'))
    
    if request.method == 'POST':
        AccessLog.query.delete()
        db.session.commit()
        flash('All access logs cleared!', 'success')
    
    return redirect(url_for('access_logs'))

# Route: Notifications
def notifications():
    """Notifications tab"""
    # For global admins, show admin notifications (user_id=None) + their own
    # For regular users, show only their own notifications
    if session.get('is_global_admin'):
        notifications_list = Notification.query.filter(
            db.or_(
                Notification.user_id == None,  # Admin notifications
                Notification.user_id == session.get('user_id')  # Own notifications
            )
        ).order_by(Notification.created_at.desc()).all()
    else:
        notifications_list = Notification.query.filter_by(
            user_id=session.get('user_id')
        ).order_by(Notification.created_at.desc()).all()
    
    return render_template('notifications.html', notifications=notifications_list)

def mark_notification_read(notification_id):
    """Mark notification as read"""
    notif = Notification.query.get_or_404(notification_id)
    
    # Check ownership
    # Global admins can mark any notification (including admin notifications with user_id=None)
    # Project site admins can only mark their own notifications
    if session.get('is_global_admin'):
        # Global admin can mark any notification
        pass
    elif notif.user_id != session.get('user_id'):
        # Regular user trying to mark someone else's notification
        return jsonify({'error': 'Permission denied'}), 403
    
    notif.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})

def delete_notification(notification_id):
    """Delete a notification (Admin can delete any, project site accounts can delete their own)"""
    notif = Notification.query.get(notification_id)
    if not notif:
        if request.method == 'POST':
            return jsonify({'error': f'Notification with ID {notification_id} not found'}), 404
        flash('Notification not found', 'error')
        return redirect(url_for('notifications'))
    
    # Check permissions
    is_global_admin = session.get('is_global_admin', False)
    user_id = session.get('user_id')
    
    # Global admins can delete any notification
    # Project site accounts can only delete their own notifications
    if not is_global_admin:
        if notif.user_id != user_id:
            if request.method == 'POST':
                return jsonify({'error': 'Permission denied. You can only delete your own notifications.'}), 403
            flash('Permission denied. You can only delete your own notifications.', 'error')
            return redirect(url_for('notifications'))
    
    try:
        db.session.delete(notif)
        db.session.commit()
        
        if request.method == 'POST':
            return jsonify({'success': True, 'message': 'Notification deleted successfully!'})
        
        flash('Notification deleted successfully!', 'success')
        return redirect(url_for('notifications'))
    except Exception as e:
        db.session.rollback()
        if request.method == 'POST':
            return jsonify({'error': f'Failed to delete notification: {str(e)}'}), 500
        flash(f'Error deleting notification: {str(e)}', 'error')
        return redirect(url_for('notifications'))

def check_notifications():
    """API endpoint to check for new unread notifications (for real-time updates)"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # For global admins, check notifications with user_id=None (admin notifications) OR their own
    # For project site admins, check their own notifications
    if session.get('is_global_admin'):
        unread_notifications = Notification.query.filter(
            db.or_(
                Notification.user_id == None,  # Admin notifications
                Notification.user_id == session.get('user_id')  # Own notifications
            ),
            Notification.is_read == False
        ).order_by(Notification.created_at.desc()).limit(10).all()
    else:
        unread_notifications = Notification.query.filter_by(
            user_id=session.get('user_id'),
            is_read=False
        ).order_by(Notification.created_at.desc()).limit(10).all()
    
    notifications_data = [{
        'id': notif.id,
        'title': notif.title,
        'message': notif.message,
        'type': notif.notification_type,
        'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for notif in unread_notifications]
    
    return jsonify({
        'notifications': notifications_data,
        'count': len(notifications_data)
    })

