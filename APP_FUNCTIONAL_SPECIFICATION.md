# Istrom Inventory Management System - Complete Functional Specification

## Overview
This is a construction inventory management system for managing materials, labor, budgets, and requests across multiple project sites. The system supports two user types: Administrators (full access) and Project Site Users (limited access).

---

## Authentication & Access Control

### Login System
- **Single Access Code Authentication**: Users enter one access code to log in
- **Access Code Types**:
  - **Global Admin Code**: Grants full system administrator access across all projects
  - **Project Site Codes**: 
    - User code: Grants limited access to specific project site
    - Admin code: Grants admin access to specific project site only
- **Session Persistence**: Sessions are saved to browser cookies and persist across browser sessions (no timeout)
- **Session Information Display**: Shows "Session: Persistent" in header

### User Types
1. **Admin Users**:
   - Full system access
   - Can view/manage all project sites
   - Can add/edit/delete inventory items
   - Can approve/reject requests
   - Access to Admin Settings tab

2. **Project Site Users**:
   - Read-only access to inventory management
   - Can view inventory for their assigned project site
   - Can submit requests for items
   - Can view their own requests and notifications
   - Cannot approve/reject requests

---

## UI Layout & Navigation

### Page Structure
- **Layout**: Wide layout mode (full width)
- **Sidebar**: Collapsed by default, contains:
  - System header with gradient background (purple gradient: #667eea to #764ba2)
  - User Information Card showing:
    - User's full name
    - User role (Admin/User) with color-coded badge
      - Admin: Green background (#dcfce7), dark green text (#166534)
      - User: Blue background (#dbeafe), dark blue text (#1e40af)
  - Current Project Site information box
  - Logout button (full width, red button)
  
- **Main Header**: Large purple gradient header displaying:
  - System title: "Istrom Inventory Management System"
  - Welcome message with user name, project site, and session status

### Tab System
The application uses a tabbed interface. **Different tabs are shown based on user type:**

**For Admin Users:**
1. Manual Entry (Budget Builder)
2. Inventory
3. Make Request
4. Review & History
5. Budget Summary
6. Actuals
7. Admin Settings

**For Project Site Users:**
1. Manual Entry (Budget Builder)
2. Inventory
3. Make Request
4. Review & History
5. Budget Summary
6. Actuals
7. Notifications

**Tab Persistence**: The system remembers which tab you were on using browser session storage and URL parameters.

---

## TAB 1: Manual Entry (Budget Builder)

### Purpose
Primary interface for adding new inventory items with proper categorization, budget assignment, and project context.

### Layout Structure

#### Section 1: Project Context (Above Form)
Three-column layout with dropdowns that update immediately:

**Column 1: Building Type Selector**
- Dropdown selectbox
- Options:
  - (Empty/Blank option)
  - Flats
  - Terraces
  - Semi-detached
  - Fully-detached
- Default: "Flats" (index 1)
- Help text: "Select building type first"
- Key: `building_type_select`

**Column 2: Section Selector**
- Dropdown selectbox
- Options (Construction sections):
  - "SUBSTRUCTURE (GROUND TO DPC LEVEL)"
  - "SUBSTRUCTURE (EXCAVATION TO DPC LEVEL)"
  - "TERRACES (6-UNITS) DPC(TERRACE SUBSTRUCTURE)"
  - "SUPERSTRUCTURE: GROUND FLOOR; (COLUMN, LINTEL AND BLOCK WORK)"
  - "SUPERSTRUCTURE, GROUND FLOOR; (SLAB,BEAMS AND STAIR CASE)"
  - "SUPERSTRUCTURE, FIRST FLOOR; (COLUMN, LINTEL AND BLOCK WORK)"
  - "SUPERSTRUCTURE FIRST FLOOR SLAB WORK (SLAB, BEAMS & STAIRCASE)"
  - "SUPERSTRUCTURE, 1ST FLOOR; (COLUMN, LINTEL, BLOCK WORK AND LIFT SHIFT)"
- Default: First option (index 0)
- Help text: "Select construction section"
- Key: `manual_section_selectbox`

**Column 3: Budget Label Selector**
- Dropdown selectbox
- **Dynamic filtering**: Budget options are filtered based on selected Building Type
- **Budget Format**: `Budget {number} - {BuildingType}({Subgroup})`
  - Example: "Budget 1 - Flats(General Materials)"
  - Example: "Budget 1 - Terraces(Woods)"
- **Subgroups Available**:
  - General Materials
  - Woods
  - Plumbings
  - Irons
  - Labour
  - Electrical (for Budget 3 and above)
  - Mechanical (for Budget 3 and above)
- **Generation Logic**:
  - Budgets 1-20 are automatically generated
  - For each budget number (1-20), all building types get all subgroups
  - Budgets from database are also included
- **Filtering Behavior**:
  - When building type is selected, only budgets matching that building type are shown
  - Example: Selecting "Flats" shows only "Budget X - Flats(...)" options
  - If no matching budgets found, shows all budgets with warning message
- **Caption**: Shows count of filtered budgets vs total budgets
- Default: First option (index 0)
- Help text: "Select budget type"
- Key: `budget_selectbox`

**Permission Check**: 
- Non-admin users see warning: "Read-Only Access: You can view items but cannot add, edit, or delete them."
- Non-admin users see info message: "Contact an administrator if you need to make changes to the inventory."

#### Section 2: Add Item Form
Form with submit button, does NOT clear on submit:

**Row 1: Item Details (4 columns)**
- Column 1: **Item Name** (text input, width: 2x)
  - Placeholder: "e.g., STONE DUST"
  - Key: `manual_name_input`
  
- Column 2: **Quantity** (number input, width: 1x)
  - Min value: 0.0
  - Step: 1.0
  - Default: 0.0
  - Key: `manual_qty_input`
  
- Column 3: **Unit** (text input, width: 1x)
  - Placeholder: "e.g., trips, pcs, bags"
  - Key: `manual_unit_input`
  
- Column 4: **Unit Cost** (number input, width: 1x)
  - Min value: 0.0
  - Step: 100.0
  - Default: 0.0
  - Prefix: "₦" (Naira symbol)
  - Key: `manual_rate_input`

**Row 2: Category Selector**
- Single selectbox
- Options:
  - Materials
  - Labour
  - Material/Labour
- Default: "Materials" (index 0)
- Help text: "Select category"
- Key: `manual_category_select`

**Automatic Group Assignment**:
- If "Materials" selected → Group = "Materials"
- If "Labour" selected → Group = "Labour"
- If "Material/Labour" selected → Group = "Material/Labour"
- **Exception**: If budget contains subgroup in parentheses like "Budget 1 - Flats(Plumbings)", it extracts:
  - "Plumbings" → converts to "MATERIAL(PLUMBINGS)"
  - "Woods" → converts to "MATERIAL(WOODS)"
  - "Irons" → converts to "MATERIAL(IRONS)"
  - This overrides the category-based group assignment

**Line Amount Preview**:
- Large centered display showing calculated total
- Format: "Line Amount: ₦{amount:,.2f}"
- Background: Light gray (#f8fafc)
- Font size: 1.4rem, bold (600 weight)
- Updates in real-time as quantity/cost changes

**Submit Button**:
- Primary style button
- Text: "Add Item"
- Width: Full container width
- On submit:
  - Validates admin access
  - Parses budget string to extract subgroup and building type
  - Creates item with all context (budget, section, group, building_type, project_site)
  - Shows success message with item details
  - Shows info message: "💡 This item will now appear in the Budget Summary tab for automatic calculations!"
  - Does NOT auto-refresh page (natural Streamlit refresh)

#### Section 3: Budget View & Totals

**Subsection: Filters (2 columns)**
- Column 1: **Budget Filter** dropdown
  - Shows all budget options (same generation logic as above)
  - Includes "All" option at top
  - Help: "Select budget to filter (shows all subgroups)"
  - Key: `budget_filter_selectbox`
  - **Hierarchical Filtering**:
    - If specific subgroup selected (e.g., "Budget 1 - Flats(General Materials)"), shows only exact matches
    - If base budget selected (e.g., "Budget 1 - Flats"), shows all subgroups under that budget
  
- Column 2: **Section Filter** dropdown
  - Includes empty option at top
  - Shows all construction sections (same list as Section selector)
  - Includes dynamic sections from database
  - Help: "Select or type custom section"
  - Key: `section_filter_selectbox`

**Filtered Items Table**:
- Columns displayed:
  - budget
  - section
  - grp (group)
  - building_type
  - name
  - qty
  - unit
  - unit_cost (formatted as currency: ₦%,.2f)
  - Amount (calculated: qty × unit_cost, formatted as currency: ₦%,.2f)
- **Pagination**: If more than 50 items, shows page selector (1-N pages)
- Shows caption: "Showing X-Y of Z items"

**Total Amount Display**:
- Large centered display
- Format: "Total Amount: ₦{total:,.2f}"
- Same styling as Line Amount Preview

**Export Button**:
- Download button
- Text: "📥 Download CSV"
- Exports filtered items as CSV file
- Filename: "budget_view.csv"

---

## TAB 2: Inventory

### Purpose
View, filter, search, and edit all inventory items. Admin-only editing capabilities.

### Layout Structure

#### Permission Warning (Non-Admins)
- Warning box: "Read-Only Access: You can view inventory but cannot modify items."
- Info box: "Contact an administrator if you need to make changes to the inventory."

#### Section 1: Loading
- Spinner with "Loading inventory..." message
- If no items: Shows info message "📦 No items found yet. Add some items in the Manual Entry tab to get started." and stops execution

#### Section 2: Quick Stats Dashboard (4 columns)
- **Total Items**: Count of all items (formatted with commas)
- **Total Value**: Sum of all item amounts (formatted as currency with ₦)
- **Materials**: Count of items where category = 'materials'
- **Labour**: Count of items where category = 'labour'

#### Section 3: Filters (3 columns)
- Column 1: **Budget Filter**
  - Dropdown with "All" option + all budget options
  - Same hierarchical filtering as Manual Entry tab
  - Help: "Select budget to filter by (shows all subgroups)"
  - Key: `inventory_budget_filter`
  
- Column 2: **Section Filter**
  - Dropdown with "All" option + all sections from database
  - Help: "Select section to filter by"
  - Key: `inventory_section_filter`
  
- Column 3: **Building Type Filter**
  - Dropdown with "All" option + PROPERTY_TYPES
  - Help: "Select building type to filter by"
  - Key: `inventory_building_type_filter`

#### Section 4: Debug Information (Caption)
- Shows: "🔍 Total items before filtering: {count}"
- If budget filter active: "🔍 Budget filter: '{filter_value}'"
- After filtering: "🔍 After budget filter: {count} items"
- If items found: "🔍 Sample budgets found: {list}"

#### Section 5: Filtered Inventory Table
- **Columns**:
  - ID
  - Name
  - Code
  - Category
  - Quantity
  - Unit
  - Unit Cost (formatted as currency)
  - Amount (calculated, formatted as currency)
  - Budget
  - Section
  - Group
  - Building Type
  - Project Site
- **Row Actions** (Admin only):
  - Edit button appears on each row
  - Delete button appears on each row

#### Section 6: Edit Item Modal/Form (Admin Only)
When Edit button clicked:
- Shows form with:
  - Item Name (read-only or editable)
  - Current Quantity display
  - New Quantity input (number, min 0.0)
  - Current Unit Cost display
  - New Unit Cost input (number, min 0.0)
- **Change Preview** (3 metric cards):
  - Old Amount: ₦{old_amount}
  - New Amount: ₦{new_amount}
  - Change: ₦{change} with delta
- Submit button: "💾 Update Item"
- On success:
  - Shows success message
  - Triggers notification system
  - Clears cache
  - Does NOT auto-refresh

#### Section 7: Danger Zone (Admin Only)
- Checkbox: "Also clear deleted request logs"
- Button: "🗑️ Delete ALL inventory and requests"
- **Two-click confirmation**: Must click twice to confirm
- Warning message on first click
- On confirm: Deletes all items and requests, shows success message
- Caption: "Tip: Use Manual Entry / Import to populate budgets; use Make Request to deduct stock later."

---

## TAB 3: Make Request

### Purpose
Submit requests for items from inventory. Available to all users.

### Layout Structure

#### Section 1: Request Details Form

**Row 1: Item Selection**
- Large selectbox: "Select Item"
- Options format: "{Item Name} ({Item Code or 'No Code'})"
- Filters items by current project site
- If no items: Shows error "No items available for request"

**Row 2: Request Context (3 columns)**
- Column 1: **Section** dropdown
  - Options: "materials", "labour"
  - Pre-populated based on item category if available
  
- Column 2: **Building Type** dropdown
  - Options: Same PROPERTY_TYPES (Flats, Terraces, Semi-detached, Fully-detached)
  - Pre-populated from item if available
  
- Column 3: **Budget** dropdown
  - Shows all budget options (filtered by building type if selected)
  - Pre-populated from item if available

**Row 3: Request Details**
- **Requested By**: Text input (required)
  - Pre-filled with user's full name from session
- **Quantity**: Number input (required, min 0.1, step 0.1, default 1.0)
- **Current Rate**: Number input (optional)
  - Pre-filled with item's current unit_cost
  - Can be edited if price changed
- **Note**: Text area (required)
  - Multi-line text input for request explanation

#### Section 2: Request Summary
Shows three metric cards:
- **Planned Rate**: Item's original unit_cost from inventory
- **Current Rate**: Selected or entered current price
- **Quantity**: Requested quantity

**Total Cost Display**:
- Large centered: "Total Cost (Current Rate): ₦{total:,.2f}"
- Calculated as: Quantity × Current Rate

**Selected Items Section**:
- Success box showing:
  - Item name (bold)
  - Quantity
  - Total cost

**Price Difference Alert** (if applicable):
- If Current Rate ≠ Planned Rate:
  - Shows info box with:
    - Price increase/decrease amount
    - Percentage change
    - Example: "Price increased by ₦500.00 (+5.0%)"

#### Section 3: Submit Request
- Primary button: "Submit Request"
- Full width
- **Validation**:
  - Requested By required
  - Note required
  - Item must be selected
  - Quantity > 0
  - Section must be selected
  - Building Type must be selected
  - Budget must be selected
- On success:
  - Shows success message with request ID
  - Shows info: "Your request will be reviewed by an administrator. Check the Review & History tab for updates."
  - Triggers notification for both requester and admin
  - Clears cache
- On error: Shows specific validation error message

---

## TAB 4: Review & History

### Purpose
View request history, approve/reject requests (admin only), delete requests.

### Layout Structure

#### Admin View

**Status Filter**:
- Dropdown: "Filter by status"
- Options: "All", "Pending", "Approved", "Rejected"
- Default: "Pending" (index 1)

**Requests Table**:
- Columns:
  - ID
  - Time (formatted as YYYY-MM-DD HH:MM)
  - Item
  - Quantity
  - Planned Price (from item unit_cost)
  - Current Price (from request current_price, falls back to planned price)
  - Total Price (Quantity × Current Price)
  - Requested By
  - Project Site
  - Building Type & Budget (formatted as "{building_type} - {budget} ({group})")
  - Status
  - Approved By
  - Note

**Statistics (4 columns)**:
- Pending count
- Approved count
- Rejected count
- Total count

**Delete Actions Section**:
- Only shows Approved or Rejected requests
- Table-like layout for delete buttons
- Each row shows:
  - ID
  - Time
  - Item
  - Quantity
  - Requested By
  - Project Site (for admin)
  - Status (color-coded: Approved=green, Rejected=red)
  - Approved By
  - Building Type & Budget
  - Delete button (🗑️)
- Delete button only enabled for:
  - Admins (can delete any request)
  - Request owner (can delete their own approved/rejected requests)

**Approve/Reject Section** (Admin only):
- For each Pending request, shows:
  - Request details
  - Approve button (green)
  - Reject button (red)
- On approve/reject:
  - Updates status
  - Records approver name
  - Updates timestamp
  - Triggers notifications

#### Project Site User View

**Request Statistics** (4 columns):
- Total Submitted
- Pending
- Approved
- Rejected

**Recent Requests Table**:
- Shows last 10 requests
- Columns:
  - ID
  - Time
  - Item
  - Quantity
  - Planned Price
  - Current Price
  - Total Price
  - Building Type & Budget
  - Status
  - Approved By
  - Note
- Info message: "Only administrators can approve or reject requests."

---

## TAB 5: Budget Summary

### Purpose
Comprehensive overview of all budgets, totals by building type, and individual budget breakdowns.

### Layout Structure

#### Section 1: Quick Overview (4 columns)
- Total Items: Count
- Total Amount: Sum of all item amounts (formatted as currency)
- Active Budgets: Count of unique budgets
- Building Types: Count of unique building types

#### Section 2: Recent Items Added
- Table showing last 5 items added
- Columns: name, budget, building_type, Amount

#### Section 3: Summary Table
- Aggregated by Budget Number and Building Type
- Columns:
  - Budget (e.g., "Budget 1")
  - Flats (total amount for Flats in this budget)
  - Terraces (total amount for Terraces in this budget)
  - Semi-detached (total amount for Semi-detached in this budget)
  - Fully-detached (total amount for Fully-detached in this budget)
  - Total (sum across all building types for this budget)
- All amounts formatted as currency: ₦{amount:,.2f}

**Grand Total Display**:
- Large centered: "Grand Total (All Budgets): ₦{total:,.2f}"
- Sums all budget totals

**Export Button**:
- "📥 Download Summary CSV"
- Exports summary table

#### Section 4: Manual Budget Summary
- **Tabbed Interface**: Creates tabs for Budget 1 through Budget 20 (or max_budget_num)
- Each tab shows:
  - **Budget {N} Summary** header
  - **Total Amount** metric for that budget
  - **Breakdown by Building Type**:
    - Metric card for each building type (Flats, Terraces, etc.)
    - Shows total amount for that building type within this budget
    - Only shows building types that have items
  - If no items: Info message "No items found for Budget {N}"

**Note**: The max_budget_num can be configured (default 20, stored in session state).

---

## TAB 6: Actuals

### Purpose
Compare planned budget vs actual costs and usage for each budget.

### Layout Structure

#### Section 1: Budget Selection
- Large dropdown: "Choose a budget to view:"
- Options format: "Budget {1-20} - {Building Type}"
- Generates all combinations:
  - Budgets 1-20
  - Building Types: Flats, Terraces, Semi-detached, Fully-Detached
- Example options:
  - "Budget 1 - Flats"
  - "Budget 1 - Terraces"
  - "Budget 2 - Flats"
  - etc.

#### Section 2: Budget vs Actual Comparison
When budget selected:

**Header**:
- Shows selected budget name
- "📊 BUDGET vs ACTUAL COMPARISON" subtitle

**Two-Column Layout**:

**Left Column: PLANNED BUDGET**
- Groups items by Category (grp field)
- For each category:
  - **Category Header** (bold): e.g., "MATERIAL(PLUMBINGS)"
  - **Table** with columns:
    - S/N (sequential number)
    - Item (item name)
    - Qty (quantity, formatted to 1 decimal)
    - Unit Cost (formatted as currency)
    - Total Cost (formatted as currency, calculated)
  - **Category Total**: "**{Category} Total: ₦{amount:,.2f}**"
  - Horizontal divider

**Right Column: ACTUALS**
- Same structure as Planned Budget
- Shows actual quantities and costs from actuals table
- If no actuals recorded:
  - Shows 0.00 for quantities and costs
- **Category Totals**: Sums actual costs for each category

**Bottom: Comparison Metrics (2 columns)**
- **Total Planned**: Sum of all planned budget amounts
- **Total Actual**: Sum of all actual costs recorded
- Both formatted as currency with metric cards

**Data Logic**:
- Planned data comes from items table filtered by budget
- Actual data comes from actuals table, linked by item_id
- Actuals are summed if multiple entries exist for same item

#### Empty States
- If no items for budget: "No items found for this budget."
- If no items for project site: "📦 No items found for this project site."
  - Additional info: "💡 Add items, create requests, and approve them to see actuals here."

**Permissions**:
- Non-admin users see: "👤 User Access: You can view actuals but cannot modify them."

---

## TAB 7A: Admin Settings (Admin Only)

### Purpose
System administration, user management, access code management, project site management.

### Layout Structure

#### Section 1: System Overview (4 columns)
- **Project Sites**: Count of active project sites
- **Total Items**: Count of all inventory items
- **Total Requests**: Count of all requests
- **Today's Access**: Count of access logs for today (Lagos timezone)

#### Section 2: Access Code Management
**Global Admin Code**:
- Current code display (masked for security)
- Update form with:
  - New Admin Code input (password type)
  - Update button
- Shows success notification on update

**Project Site Access Codes**:
- Dropdown: "Select Project Site"
  - Shows all project sites
- For selected site:
  - Shows current User Code (masked)
  - Shows current Admin Code (masked)
  - Update form for both codes
  - Update button

#### Section 3: Project Site Management
**Current Project Site**:
- Dropdown: "Switch Project Site"
  - Shows all project sites
  - Current selection highlighted
- Info message about current selection

**Add New Project Site**:
- Form with:
  - Project Site Name (text input)
  - Description (text area, optional)
- Add button
- On success:
  - Creates new project site
  - Triggers notification
  - Info: "💡 You can now switch to this project site using the dropdown above."

#### Section 4: Access Logs (Expandable Section)
**Filters**:
- Role Filter: Dropdown ("All", "admin", "project_site", "unknown")
- Last N Days: Number input (1-365, default 7)
- Refresh button

**Clear All Logs**:
- Warning box: "This will delete ALL access logs and start fresh. This action cannot be undone!"
- "Clear ALL Logs" button (primary style)

**Quick Overview (4 columns)**:
- Total Logs
- Today's Access
- Failed Attempts
- Unique Users

**Access Log Details**:
- Table with columns:
  - User
  - Role (capitalized)
  - Access Code (masked or shown)
  - Date & Time (formatted as YYYY-MM-DD HH:MM:SS)
  - Status ("✓ Success" or "✗ Failed")
- **Pagination**: 20 logs per page with page selector
- Shows caption: "Showing X-Y of Z logs"

**Access Statistics (4 columns)**:
- Total Access
- Successful (with percentage delta)
- Failed (with percentage delta)
- Unique Users

---

## TAB 7B: Notifications (Project Site Users Only)

### Purpose
View system notifications, approval/rejection notices, and mark notifications as read.

### Layout Structure

#### Notifications List
- Each notification shown as expandable item
- Format: "{Title} - {Created At timestamp}"
- When expanded:
  - Notification message
  - Notification type
  - Created timestamp
  - "Mark as Read" button (if unread)

**Notification Types**:
- request: Request-related notifications
- approval: Request approval notifications
- rejection: Request rejection notifications
- system: System notifications

**Read Status**:
- Unread notifications have distinct styling (border highlight)
- Read notifications are grayed out

---

## Data Models & Relationships

### Items Table
**Fields**:
- id (primary key)
- code (optional, item code/SKU)
- name (required, item name)
- category (required, 'materials' or 'labour')
- unit (optional, e.g., "trips", "pcs", "bags")
- qty (required, numeric, default 0)
- unit_cost (optional, numeric, unit price)
- budget (text, format: "Budget {N} - {BuildingType}({Subgroup})")
- section (text, construction section name)
- grp (text, group/category like "Materials", "MATERIAL(PLUMBINGS)")
- building_type (text, one of: Flats, Terraces, Semi-detached, Fully-detached)
- project_site (text, links to project_sites table)
- created_at (timestamp)

### Requests Table
**Fields**:
- id (primary key)
- ts (timestamp, request timestamp)
- section ('materials' or 'labour')
- item_id (foreign key to items)
- qty (numeric, requested quantity)
- requested_by (text, user's full name)
- note (text, request notes/explanation)
- status ('Pending', 'Approved', 'Rejected', default 'Pending')
- approved_by (text, admin who approved/rejected)
- current_price (numeric, actual price at time of request, optional)
- created_at (timestamp)
- updated_at (timestamp)

### Notifications Table
**Fields**:
- id (primary key)
- notification_type (text)
- title (text)
- message (text)
- user_id (foreign key to users, optional)
- request_id (foreign key to requests, optional)
- is_read (boolean, default false)
- created_at (timestamp)

### Actuals Table
**Fields**:
- id (primary key)
- item_id (foreign key to items)
- actual_qty (numeric, actual quantity used)
- actual_cost (numeric, actual cost incurred)
- actual_date (text/date, when actual occurred)
- recorded_by (text, who recorded the actual)
- notes (text, optional notes)
- project_site (text)
- created_at (timestamp)

---

## Budget System Logic

### Budget Naming Convention
**Format**: `Budget {number} - {BuildingType}({Subgroup})`

**Examples**:
- "Budget 1 - Flats(General Materials)"
- "Budget 1 - Terraces(Woods)"
- "Budget 2 - Semi-detached(Plumbings)"
- "Budget 3 - Fully-detached(Electrical)"
- "Budget 5 - Flats(Labour)"

### Budget Hierarchy
1. **Base Budget**: "Budget {N} - {BuildingType}"
   - When filtered, shows ALL subgroups under this budget
   - Example: "Budget 1 - Flats" shows:
     - Budget 1 - Flats(General Materials)
     - Budget 1 - Flats(Woods)
     - Budget 1 - Flats(Plumbings)
     - Budget 1 - Flats(Irons)
     - Budget 1 - Flats(Labour)

2. **Specific Subgroup**: "Budget {N} - {BuildingType}({Subgroup})"
   - When filtered, shows ONLY exact matches
   - Example: "Budget 1 - Flats(General Materials)" shows only items with that exact budget string

### Budget Generation
- **Automatic**: Budgets 1-20 are pre-generated for all building types and subgroups
- **Subgroups for Budgets 1-2**: General Materials, Woods, Plumbings, Irons, Labour
- **Subgroups for Budgets 3-20**: All of above PLUS Electrical, Mechanical
- **Database Integration**: Budgets found in database are added to the list
- **Dynamic Range**: Maximum budget number configurable (default 20, stored in session state as `max_budget_num`)

### Budget Filtering Logic
- **Normalization**: Budget strings are normalized (lowercase, trim spaces, handle spacing around parentheses)
- **Case Insensitive**: Matching is case-insensitive
- **Flexible Matching**: Handles variations like "Iron" vs "Irons"
- **Hierarchical Matching**: Base budgets match all subgroups, specific subgroups match exactly

---

## Notification System

### Client-Side Notification System
- **JavaScript-based**: Runs in browser
- **Toast Notifications**: Slide-in from right, auto-dismiss after 3-4 seconds
- **Sound Alerts**: Plays beep sound (800Hz tone)
- **Notification Types**:
  - Success (green background)
  - Error (red background)
  - Warning (orange background)
  - Info (blue background)

### Notification Triggers
- Item added
- Item updated
- Item deleted
- Request submitted
- Request approved
- Request rejected
- Access code updated
- Project site added

### Notification Storage
- Uses browser localStorage
- Keys: `request_approved_notification`, `item_added_notification`, etc.
- Checked on page load and every 30 seconds
- Cleared after being displayed

---

## Currency Formatting

### Display Format
- **Symbol**: ₦ (Naira)
- **Format**: `₦{amount:,.2f}`
- **Examples**:
  - 1000 → "₦1,000.00"
  - 12345.67 → "₦12,345.67"
  - 1000000 → "₦1,000,000.00"

### All Amount Fields
- Unit Cost
- Total Cost
- Amount
- Line Amount
- Category Totals
- Budget Totals
- Grand Totals
- Planned vs Actual comparisons

---

## Color Scheme & Styling

### Primary Colors
- **Purple Gradient**: #667eea → #764ba2 (headers, sidebar, active elements)
- **Success Green**: #dcfce7 background, #166534 text (admin badges, success messages)
- **Info Blue**: #dbeafe background, #1e40af text (user badges, info messages)
- **Error Red**: #fef2f2 background, #dc2626 text (error messages, delete buttons)
- **Warning Orange**: #fffbeb background, #d97706 text (warnings)

### Typography
- **Headers**: 2.5rem, bold (700 weight)
- **Subheaders**: 1.5rem, semibold (600 weight)
- **Body**: System font stack (-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto)
- **Metrics**: 2rem, bold (700 weight) for large numbers

### Spacing & Layout
- **Padding**: 1rem standard, 2rem for headers
- **Border Radius**: 8px standard, 10px for headers
- **Shadows**: Subtle box shadows (0 1px 3px rgba(0,0,0,0.1))
- **Columns**: Responsive column layouts using Streamlit's column system

---

## User Experience Features

### Tab Persistence
- Current tab saved to browser sessionStorage
- Restored on page reload
- URL parameters also used for tab state

### Loading States
- Spinners with descriptive messages:
  - "Loading inventory..."
  - "Loading budget summary data..."
  - "Authenticating..."
- Progress indicators for long operations

### Error Handling
- User-friendly error messages
- Validation feedback on forms
- Graceful handling of empty states
- Info messages for guidance

### Success Feedback
- Success messages after operations
- Notification toasts
- Sound alerts (optional)
- Visual confirmation (green checkmarks, success badges)

### Empty States
- Helpful messages when no data
- Guidance on next steps
- Links/pointers to relevant tabs

### Data Refresh
- Cache management for performance
- Manual refresh options
- Natural Streamlit reruns (no forced refreshes)

---

## Validation Rules

### Item Entry Validation
- Item Name: Required
- Quantity: Required, >= 0
- Category: Required, must be one of: Materials, Labour, Material/Labour
- Building Type: Optional but recommended
- Section: Optional but recommended
- Budget: Optional but recommended

### Request Validation
- Item Selection: Required
- Requested By: Required, non-empty
- Note: Required, non-empty
- Quantity: Required, > 0
- Section: Required
- Building Type: Required
- Budget: Required

### Access Code Validation
- Admin Code: Required, non-empty
- User Code: Required, non-empty
- Project Site: Required for project site codes

---

## Performance Optimizations

### Caching Strategy
- Budget options cached (5 minute TTL)
- Access codes cached
- Item dataframes cached per project site
- Summary data cached

### Database Queries
- Indexed on frequently filtered columns (budget, section, building_type)
- Parameterized queries for security
- Batch operations where possible

### UI Optimization
- Pagination for large datasets (50 items per page)
- Lazy loading where applicable
- Efficient filtering at database level when possible

---

## Security Features

### Authentication
- Access code-based authentication
- Session persistence via cookies
- Access logging for audit trail

### Authorization
- Role-based access control (Admin vs User)
- Project site isolation for non-admin users
- Permission checks on all write operations

### Data Protection
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS prevention (Streamlit's built-in protections)

---

This specification provides a complete blueprint for recreating the Istrom Inventory Management System with all its features, UI elements, workflows, and business logic.

