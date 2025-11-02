# Istrom Inventory Management System

A comprehensive Flask-based inventory management system for construction projects, built without Streamlit for better performance.

## Features

- **Authentication System**: Access code-based login with role-based access control
- **Manual Entry (Budget Builder)**: Add inventory items with categorization and budget assignment
- **Inventory Management**: View, filter, search, and edit all inventory items
- **Request System**: Submit and manage item requests with approval workflow
- **Budget Summary**: Comprehensive budget overview with totals and breakdowns
- **Actuals Tracking**: Compare planned budgets vs actual costs
- **Admin Settings**: Manage access codes, project sites, and view access logs
- **Notifications**: Real-time notifications for requests and updates

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application:**
   ```bash
   python app.py
   ```

3. **Access the application:**
   - Open your browser and navigate to `http://localhost:5000`
   - Default login credentials:
     - **Admin**: `admin123` (Global Admin - ONLY default access)

## Default Access Codes

When first run, the system creates **ONLY** the global admin code:
- **Global Admin Code**: `admin123` (This is the ONLY default access)

**⚠️ IMPORTANT**: 
- Change the admin code immediately in production!
- **Project sites must be created manually** through Admin Settings
- **Each project site has ONE access code** that grants admin access to that site
- **Project site access codes must be created manually** after creating a project site
- No default project sites or project site access codes are created automatically

## Project Structure

```
Inventory 2.0/
├── app.py                 # Main Flask application
├── routes.py              # Route handlers for all pages
├── models.py              # Database models
├── database.py            # Database configuration
├── utils.py               # Utility functions
├── requirements.txt        # Python dependencies
├── templates/             # HTML templates
│   ├── base.html
│   ├── login.html
│   ├── manual_entry.html
│   ├── inventory.html
│   ├── make_request.html
│   ├── review_history.html
│   ├── budget_summary.html
│   ├── actuals.html
│   ├── admin_settings.html
│   ├── notifications.html
│   └── access_logs.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── inventory.db           # SQLite database (created automatically)
```

## User Roles

### Global Admin
- Full system access across all projects
- Can manage all project sites
- Can add/edit/delete inventory items
- Can approve/reject requests
- Access to Admin Settings tab

### Project Site Admin
- Admin access to specific project site only
- Can manage inventory for their site
- Can approve/reject requests for their site

### Project Site User
- Read-only access to inventory
- Can view inventory for assigned project site
- Can submit requests for items
- Can view own requests and notifications

## Key Features

### Budget System
- Supports budgets 1-20 with multiple building types (Flats, Terraces, Semi-detached, Fully-detached)
- Subgroups: General Materials, Woods, Plumbings, Irons, Labour, Electrical, Mechanical
- Hierarchical budget filtering

### Session Management
- Persistent sessions (no timeout)
- Session stored in browser cookies
- "Session: Persistent" indicator in UI

### Notifications
- Toast notifications with sound alerts
- Real-time updates via localStorage
- Browser-based notification system

## Database

The application uses SQLite by default. The database file (`inventory.db`) is created automatically on first run.

To use a different database, update the `SQLALCHEMY_DATABASE_URI` in `app.py`.

## Security Notes

1. **Change default access codes** in production
2. **Set a strong SECRET_KEY** in production (use environment variable)
3. **Use HTTPS** in production
4. **Restrict database file permissions** if using SQLite
5. **Regular backups** of the database

## Development

To run in development mode:
```bash
python app.py
```

The app will run on `http://localhost:5000` with debug mode enabled.

## Production Deployment

For production:
1. Set `SECRET_KEY` environment variable
2. Set `FLASK_ENV=production`
3. Use a production WSGI server (e.g., Gunicorn)
4. Use a proper database (PostgreSQL, MySQL)
5. Configure reverse proxy (Nginx)
6. Enable HTTPS

## License

Proprietary - All rights reserved

