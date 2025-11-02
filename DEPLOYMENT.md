# Deployment Guide for Render

This guide will help you deploy the Istrom Inventory Management System on Render.

## Prerequisites

1. A GitHub account
2. Your code pushed to GitHub (already done: https://github.com/whoismuhd/Inventory-2.0)
3. A Render account (sign up at https://render.com)

## Deployment Steps

### Step 1: Create PostgreSQL Database on Render

1. Log into your Render dashboard
2. Click "New +" and select "PostgreSQL"
3. Configure:
   - **Name**: `istrom-inventory-db` (or any name you prefer)
   - **Database**: `istrom_inventory`
   - **User**: `istrom_user`
   - **Plan**: Free tier (for testing) or Paid (for production)
4. Click "Create Database"
5. **Save the Internal Database URL** - you'll need this later

### Step 2: Create Web Service on Render

1. In Render dashboard, click "New +" and select "Web Service"
2. Connect your GitHub repository:
   - Select "Build and deploy from a Git repository"
   - Authorize Render to access your GitHub if needed
   - Select repository: `whoismuhd/Inventory-2.0`
3. Configure the service:
   - **Name**: `istrom-inventory` (or any name)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or `/` if it asks)
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     gunicorn app:app
     ```
   - **Plan**: Free tier (for testing) or Paid (for production)

### Step 3: Configure Environment Variables

In the "Environment" section of your Web Service, add these variables:

1. **SECRET_KEY** (Required):
   - Generate a secure key:
     ```bash
     python -c "import secrets; print(secrets.token_hex(32))"
     ```
   - Or use Render's "Generate" button for this field
   - **Important**: Keep this secret!

2. **DATABASE_URL** (Required):
   - Copy the "Internal Database URL" from your PostgreSQL database
   - It should look like: `postgresql://user:password@hostname/dbname`
   - Render automatically sets this, but you can also link the database

3. **PYTHON_VERSION** (Optional but recommended):
   - Value: `3.11.0` or `3.12.0`

### Step 4: Link Database to Web Service (Optional but Recommended)

1. In your Web Service settings, go to "Environment"
2. Find "Link Database" section
3. Select your PostgreSQL database
4. This automatically sets `DATABASE_URL` for you

### Step 5: Deploy

1. Click "Create Web Service"
2. Render will start building and deploying your application
3. Monitor the build logs for any errors
4. Once deployed, your app will be available at: `https://your-service-name.onrender.com`

## Using render.yaml (Alternative Method)

If you prefer configuration as code:

1. The `render.yaml` file is already in your repository
2. In Render dashboard, click "New +" → "Blueprint"
3. Connect your GitHub repository
4. Render will read `render.yaml` and create all services automatically

## Post-Deployment

### Initial Setup

1. Visit your deployed URL
2. Log in with the default admin code: `admin123`
3. **IMPORTANT**: Change the admin code immediately via Admin Settings
4. Create your first project site
5. Set up access codes for project sites

### Database Migration

If you have existing data in SQLite:

1. Export your data from local SQLite database
2. Import into PostgreSQL database on Render
3. Or recreate the data through the admin interface

### Monitoring

- Check "Logs" tab in Render dashboard for application logs
- Monitor database performance in PostgreSQL dashboard
- Set up alerts for errors (available in paid plans)

## Troubleshooting

### Common Issues

1. **Build Fails**:
   - Check build logs for missing dependencies
   - Ensure `requirements.txt` is up to date
   - Verify Python version compatibility

2. **Application Won't Start**:
   - Check that `gunicorn` is in requirements.txt
   - Verify start command: `gunicorn app:app`
   - Check application logs for errors

3. **Database Connection Errors**:
   - Verify `DATABASE_URL` is set correctly
   - Check that database is running
   - Ensure database credentials are correct
   - Note: Use "Internal Database URL" not "External Database URL"

4. **Static Files Not Loading**:
   - Static files should work automatically
   - If issues, check `static` folder structure

5. **Session Issues**:
   - Ensure `SECRET_KEY` is set and unique
   - Don't share `SECRET_KEY` between instances

### Free Tier Limitations

- **Spinning Down**: Free tier services spin down after 15 minutes of inactivity
- **First Request**: May take 30-60 seconds to start up
- **Database**: Free PostgreSQL has 90-day retention limit
- **Performance**: Free tier has limited resources

## Production Recommendations

For production use:

1. **Upgrade to Paid Plan**: More resources and reliability
2. **Use Custom Domain**: Add your own domain name
3. **Enable HTTPS**: Automatically enabled by Render
4. **Set Up Backups**: Regular database backups
5. **Monitor Performance**: Use Render's monitoring tools
6. **Set Environment Variables**: Never commit secrets
7. **Enable Auto-Deploy**: Automatically deploy on git push

## Cost Estimate

- **Free Tier**: $0/month (limited resources, spins down)
- **Starter Plan**: $7/month per service + $7/month for database
- **Professional Plan**: $25/month per service + $20/month for database

## Support

- Render Documentation: https://render.com/docs
- Render Community: https://community.render.com
- Application Issues: Check GitHub Issues

## Security Checklist

- [ ] Change default admin code immediately
- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] Enable database backups
- [ ] Regularly update dependencies
- [ ] Use HTTPS (enabled by default on Render)
- [ ] Restrict admin access
- [ ] Monitor access logs

