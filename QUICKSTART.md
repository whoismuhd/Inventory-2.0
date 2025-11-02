# Quick Start Guide

## Running the Application

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Login:**
   - Navigate to `http://localhost:5000`
   - Default admin code: `admin123` (ONLY default access)

## First Steps

1. **Login as Admin** (code: `admin123`)
2. **Go to Admin Settings** tab
3. **Change admin access code** for security (highly recommended!)
4. **Add Project Sites** if needed
5. **Set Access Code** for each project site (one code per site)
6. **Go to Manual Entry** tab to start adding inventory items

**Note:** Project site access codes are NOT created automatically. You must:
- Create a project site
- Then manually set the access code for that site in Admin Settings
- Each project site has **ONE access code** that grants admin access to that site

## Key Tabs

- **Manual Entry**: Add new inventory items with budgets and categories
- **Inventory**: View and manage all items (filter, edit, delete)
- **Make Request**: Submit requests for items
- **Review & History**: Approve/reject requests (admin only)
- **Budget Summary**: View budget totals and breakdowns
- **Actuals**: Compare planned vs actual costs
- **Admin Settings**: Manage system (admin only)
- **Notifications**: View system notifications (users only)

## Default Data

On first run, the system automatically creates:
- **ONLY** Default global admin code: `admin123`

**Project sites and their access codes are NOT created automatically** - they must be created manually through Admin Settings.

## Database

The SQLite database (`inventory.db`) is created automatically. No manual setup required.

## Troubleshooting

- **Can't login?** Check that you're using the correct access code
- **No items showing?** Add items in the Manual Entry tab first
- **Permission denied?** Make sure you're logged in as admin for admin functions
- **Port already in use?** Change the port in `app.py` (line 213)

## Next Steps

1. Change all default access codes
2. Add your project sites
3. Add inventory items
4. Configure budgets
5. Start using the request system

For detailed documentation, see `README.md`.

