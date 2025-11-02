"""Utility functions for the inventory system"""
from datetime import datetime

PROPERTY_TYPES = ['Flats', 'Terraces', 'Semi-detached', 'Fully-detached']
SUBGROUPS_BASE = ['General Materials', 'Woods', 'Plumbings', 'Irons', 'Labour']
SUBGROUPS_EXTENDED = SUBGROUPS_BASE + ['Electrical', 'Mechanical']

def generate_budget_options(max_budget_num=20, building_type=None, existing_budgets=None):
    """Generate budget options for dropdowns"""
    options = []
    existing_budgets = existing_budgets or []
    
    # Generate budgets 1-20 for all building types and subgroups
    for budget_num in range(1, max_budget_num + 1):
        # Determine subgroups based on budget number
        subgroups = SUBGROUPS_EXTENDED if budget_num >= 3 else SUBGROUPS_BASE
        
        for building in PROPERTY_TYPES:
            for subgroup in subgroups:
                budget_str = f"Budget {budget_num} - {building}({subgroup})"
                options.append(budget_str)
    
    # Add existing budgets from database
    if existing_budgets:
        for budget in existing_budgets:
            if budget not in options:
                options.append(budget)
    
    # Filter by building type if specified
    if building_type:
        options = [opt for opt in options if f"- {building_type}(" in opt]
    
    # Sort numerically by budget number, not alphabetically
    def extract_budget_number(budget_str):
        """Extract budget number from string like 'Budget 1 - Flats(...)'"""
        try:
            # Extract number after "Budget "
            parts = budget_str.split("Budget ", 1)
            if len(parts) > 1:
                num_str = parts[1].split(" -")[0].strip()
                return int(num_str)
        except (ValueError, IndexError):
            pass
        return 999  # Put invalid formats at the end
    
    # Sort by budget number first, then alphabetically for same budget number
    return sorted(options, key=lambda x: (extract_budget_number(x), x))

def normalize_budget(budget_str):
    """Normalize budget string for comparison"""
    if not budget_str:
        return ""
    return budget_str.lower().strip().replace(" ", "")

def filter_budgets_by_type(budgets, building_type):
    """Filter budget list by building type"""
    if not building_type:
        return budgets
    return [b for b in budgets if f"- {building_type}(" in b]

def match_budget_filter(item_budget, filter_budget):
    """Check if item budget matches filter budget (hierarchical matching)"""
    if not filter_budget or filter_budget == "All":
        return True
    
    item_norm = normalize_budget(item_budget)
    filter_norm = normalize_budget(filter_budget)
    
    # Exact match
    if item_norm == filter_norm:
        return True
    
    # Hierarchical match: "Budget 1 - Flats" matches "Budget 1 - Flats(General Materials)"
    # Check if filter is a base budget (no subgroup in parentheses)
    if "(" not in filter_budget:
        # Extract base part (e.g., "Budget 1 - Flats")
        base = normalize_budget(filter_budget)
        # Check if item budget starts with this base
        if item_budget:
            item_base = normalize_budget(item_budget.split("(")[0] if "(" in item_budget else item_budget)
            return base == item_base
    
    return False

def format_currency(amount):
    """Format amount as Nigerian Naira"""
    if amount is None:
        return "₦0.00"
    try:
        return f"₦{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "₦0.00"

def calculate_line_amount(qty, unit_cost):
    """Calculate line amount"""
    try:
        qty = float(qty) if qty else 0.0
        unit_cost = float(unit_cost) if unit_cost else 0.0
        return qty * unit_cost
    except (ValueError, TypeError):
        return 0.0

def extract_budget_parts(budget_str):
    """Extract building type and subgroup from budget string"""
    if not budget_str:
        return None, None
    
    try:
        # Format: "Budget {N} - {BuildingType}({Subgroup})"
        if "(" in budget_str and ")" in budget_str:
            parts = budget_str.split("(")
            building_part = parts[0].strip()
            subgroup = parts[1].rstrip(")").strip()
            
            # Extract building type (after "Budget N -")
            if "-" in building_part:
                building_type = building_part.split("-")[-1].strip()
                return building_type, subgroup
    except Exception:
        pass
    
    return None, None

def determine_group_from_category_and_budget(category, budget):
    """Determine group based on category and budget subgroup"""
    if budget:
        building_type, subgroup = extract_budget_parts(budget)
        
        # Convert subgroup to MATERIAL format
        subgroup_map = {
            'Plumbings': 'MATERIAL(PLUMBINGS)',
            'Woods': 'MATERIAL(WOODS)',
            'Irons': 'MATERIAL(IRONS)',
            'General Materials': 'Materials',
            'Labour': 'Labour',
            'Electrical': 'MATERIAL(ELECTRICAL)',
            'Mechanical': 'MATERIAL(MECHANICAL)'
        }
        
        if subgroup and subgroup in subgroup_map:
            return subgroup_map[subgroup]
    
    # Fallback to category
    category_map = {
        'Materials': 'Materials',
        'Labour': 'Labour',
        'Material/Labour': 'Material/Labour'
    }
    
    return category_map.get(category, 'Materials')

