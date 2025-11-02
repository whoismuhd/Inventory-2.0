# Complete Render Deployment Guide - Step by Step

This guide will walk you through deploying your Istrom Inventory Management System on Render from scratch.

---

## 📋 Prerequisites Checklist

Before starting, make sure you have:
- ✅ GitHub account
- ✅ Code pushed to GitHub (repository: https://github.com/whoismuhd/Inventory-2.0)
- ✅ Email address for Render account

---

## 🚀 Step 1: Create Render Account

1. Go to **https://render.com**
2. Click **"Get Started for Free"** or **"Sign Up"**
3. Choose one of these sign-up methods:
   - **GitHub** (Recommended - easiest way to connect your repo)
   - Email
   - Google
4. Complete the sign-up process
5. Verify your email if required

---

## 💾 Step 2: Create PostgreSQL Database

### 2.1 Create Database Service

1. Once logged into Render dashboard, click the **"New +"** button (top right)
2. Select **"PostgreSQL"** from the dropdown menu

### 2.2 Configure Database

Fill in the database configuration:

- **Name**: `istrom-inventory-db` (or any name you prefer)
- **Database**: `istrom_inventory` (or leave default)
- **User**: `istrom_user` (or leave default)
- **Region**: Choose the closest region to your users
  - Options: `Oregon (US West)`, `Frankfurt (EU)`, `Singapore (Asia Pacific)`, etc.
- **PostgreSQL Version**: Leave as default (latest)
- **Plan**: 
  - **Free** - For testing (90-day data retention, shared resources)
  - **Starter ($7/month)** - For production (persistent data, better performance)

### 2.3 Create Database

1. Click **"Create Database"**
2. Wait 1-2 minutes for the database to be provisioned
3. You'll see a dashboard for your database

### 2.4 Save Database Connection Info

1. In your database dashboard, find the **"Connections"** section
2. **Copy the "Internal Database URL"** - You'll need this later!
   - It looks like: `postgresql://user:password@hostname/dbname`
   - **⚠️ IMPORTANT**: Use "Internal Database URL", NOT "External Database URL"
   - Your Internal URL: `postgresql://istrompostgre_zgkc_user:X7tmMF5MDpxAPAAhaGFuiZs6q3EeIxDd@dpg-d43q673ipnbc73c7fjlg-a/istrompostgre_zgkc`

---

## 🌐 Step 3: Create Web Service

### 3.1 Start Web Service Creation

1. In Render dashboard, click **"New +"** again
2. Select **"Web Service"** from the dropdown menu

### 3.2 Connect GitHub Repository

**Option A: Connect GitHub Account (Recommended)**
1. Click **"Connect GitHub"** or **"Connect account"**
2. Authorize Render to access your GitHub account
3. You may need to install Render GitHub App
4. Select the repository: **`whoismuhd/Inventory-2.0`**
5. Click **"Connect"**

**Option B: Public Repository (No Auth Required)**
1. Enter repository URL: `https://github.com/whoismuhd/Inventory-2.0`
2. Render will connect automatically if it's public

### 3.3 Configure Basic Settings

Fill in the basic configuration:

- **Name**: `istrom-inventory` (or any name you prefer)
  - This will be part of your URL: `https://istrom-inventory.onrender.com`
- **Region**: Same region as your database (recommended)
- **Branch**: `main` (your default branch)
- **Root Directory**: Leave **empty** (or `/` if required)
- **Runtime**: `Python 3` (auto-detected)
- **Plan**: 
  - **Free** - For testing (spins down after 15 min inactivity)
  - **Starter ($7/month)** - For production (always running)

### 3.4 Configure Build & Start Commands

Scroll down to **"Build & Deploy"** section:

**Build Command:**
```
pip install -r requirements.txt
```

**Start Command:**
```
gunicorn app:app
```

⚠️ **Important**: 
- Build command installs all dependencies
- Start command runs gunicorn (production server) with your Flask app

---

## 🔐 Step 4: Configure Environment Variables

### 4.1 Add Environment Variables

Before clicking "Create", click **"Advanced"** at the bottom, then scroll to **"Environment Variables"** section.

Click **"Add Environment Variable"** for each:

### 4.2 Variable 1: SECRET_KEY

1. **Key**: `SECRET_KEY`
2. **Value**: Generate a secure random key:
   
   **Method A (Using Python):**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Copy the output (a long random string)
   
   **Method B (Using Render's Generator):**
   - Click "Generate" button next to the value field
   - Render will generate a random key automatically
   
   **Method C (Manual):**
   - Use any random string generator
   - Should be at least 32 characters long
   - Example format: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0`

3. Click **"Save"** or check the checkbox

### 4.3 Variable 2: DATABASE_URL

1. **Key**: `DATABASE_URL`
2. **Value**: Paste your Internal Database URL:
   ```
   postgresql://istrompostgre_zgkc_user:X7tmMF5MDpxAPAAhaGFuiZs6q3EeIxDd@dpg-d43q673ipnbc73c7fjlg-a/istrompostgre_zgkc
   ```
   ⚠️ **Make sure this is the INTERNAL URL, not External!**

3. Click **"Save"** or check the checkbox

### 4.4 Variable 3: PYTHON_VERSION (Optional)

1. **Key**: `PYTHON_VERSION`
2. **Value**: `3.11.0` (or `3.12.0` if you prefer)
3. Click **"Save"** or check the checkbox

---

## 🔗 Step 5: Link Database (Alternative Method)

Instead of manually setting DATABASE_URL, you can link the database:

1. Scroll to **"Links"** section (in Advanced settings)
2. Click **"Link Resource"**
3. Select your PostgreSQL database from the dropdown
4. Click **"Link"**
5. This automatically sets `DATABASE_URL` for you (you can skip Step 4.3 if using this method)

---

## 🚀 Step 6: Deploy

### 6.1 Create Web Service

1. Scroll to the bottom
2. Review all settings:
   - ✅ Repository connected
   - ✅ Build command set
   - ✅ Start command set
   - ✅ Environment variables added
3. Click **"Create Web Service"**

### 6.2 Monitor Deployment

1. Render will start building your application
2. You'll see a build log showing progress:
   ```
   ==> Cloning from GitHub...
   ==> Building...
   ==> Installing dependencies...
   ==> Starting...
   ```
3. **First deployment takes 5-10 minutes**
4. Watch for any errors in the logs

### 6.3 Build Success Indicators

Look for these messages in logs:
- ✅ `Successfully installed ...`
- ✅ `[INFO] Starting gunicorn ...`
- ✅ `Listening at: http://0.0.0.0:xxxx`
- ✅ `Your service is live at https://...`

---

## ✅ Step 7: Test Deployment

### 7.1 Access Your Application

1. Once deployment completes, you'll see your service URL
2. It will be: `https://your-service-name.onrender.com`
3. Click the URL or copy it

### 7.2 Initial Setup

1. **First Visit**: The page may take 30-60 seconds to load (free tier spins up on first request)
2. **Login Page**: You should see the Istrom login page
3. **Default Admin Code**: `admin123`
4. **Log In**: Enter `admin123` and click login

### 7.3 Security: Change Admin Code

**⚠️ IMPORTANT - Do this immediately!**

1. Once logged in, go to **"Admin Settings"** tab
2. Find **"Access Code Management"** section
3. Click to expand
4. Enter a new admin code
5. Click **"Update Admin Code"**
6. **Save this code securely!**

### 7.4 Create Project Site

1. In Admin Settings, go to **"Project Site Management"**
2. Click **"Add New Project Site"**
3. Fill in:
   - **Project Site Name**: e.g., "Downtown Plaza"
   - **Description**: (Optional)
   - **Access Code**: Create a code for this site
4. Click **"Add Project Site"**

---

## 🔍 Step 8: Verify Everything Works

Test these features:

1. ✅ **Login/Logout** - Works correctly
2. ✅ **Manual Entry** - Can add items
3. ✅ **Inventory** - Can view and edit items
4. ✅ **Make Request** - Can create requests
5. ✅ **Review & History** - Can approve/reject requests
6. ✅ **Notifications** - Can see notifications
7. ✅ **Budget Summary** - Can view budgets
8. ✅ **Actuals** - Can view actuals

---

## 🐛 Troubleshooting Common Issues

### Issue: Build Fails

**Symptoms**: Build log shows errors, deployment stops

**Solutions**:
1. Check build logs for specific error messages
2. Verify `requirements.txt` has all dependencies
3. Ensure Python version is compatible (3.11+)
4. Common fixes:
   - Missing dependency → Add to `requirements.txt`
   - Version conflict → Update versions in `requirements.txt`

### Issue: Application Won't Start

**Symptoms**: Build succeeds but service shows "Error" status

**Solutions**:
1. Check **"Logs"** tab for application errors
2. Verify start command: `gunicorn app:app`
3. Ensure `gunicorn` is in `requirements.txt`
4. Check for database connection errors

### Issue: Database Connection Error

**Symptoms**: App loads but shows database errors

**Solutions**:
1. Verify `DATABASE_URL` is set correctly
2. Ensure you're using **INTERNAL** Database URL (not external)
3. Check that database service is running
4. Verify URL format: starts with `postgresql://` (not `postgres://`)
5. Try linking database via "Links" section instead

### Issue: 502 Bad Gateway

**Symptoms**: Page shows "502 Bad Gateway" error

**Solutions**:
1. Wait 30-60 seconds (free tier needs time to wake up)
2. Refresh the page
3. Check application logs for errors
4. Verify database connection

### Issue: Static Files Not Loading

**Symptoms**: Page loads but CSS/JS not working

**Solutions**:
1. Static files should work automatically
2. Check browser console for 404 errors
3. Verify `static/` folder structure in repository
4. Clear browser cache and refresh

---

## 📊 Step 9: Monitor Your Deployment

### 9.1 View Logs

1. In your service dashboard, click **"Logs"** tab
2. View real-time application logs
3. Useful for debugging and monitoring

### 9.2 Check Service Status

- **Live** (green) = Running correctly
- **Deploying** (yellow) = Currently building
- **Error** (red) = Something went wrong, check logs

### 9.3 Database Monitoring

1. Go to your PostgreSQL database dashboard
2. Check **"Metrics"** for usage stats
3. View **"Logs"** for database activity

---

## 🔒 Step 10: Security Checklist

After deployment, ensure:

- [ ] Changed default admin code (`admin123`)
- [ ] SECRET_KEY is set and unique
- [ ] Database credentials are secure
- [ ] HTTPS is enabled (automatic on Render)
- [ ] Regular backups configured (for production)
- [ ] Access logs are monitored

---

## 💰 Pricing Reference

### Free Tier (Testing)
- **Web Service**: Free (spins down after 15 min inactivity)
- **Database**: Free (90-day data retention)
- **Total**: $0/month
- **Limitations**: Cold starts, limited resources

### Starter Tier (Production)
- **Web Service**: $7/month (always running)
- **Database**: $7/month (persistent data)
- **Total**: ~$14/month
- **Benefits**: No cold starts, better performance

### Professional Tier (Enterprise)
- **Web Service**: $25/month
- **Database**: $20/month
- **Total**: ~$45/month
- **Benefits**: More resources, priority support

---

## 📞 Next Steps

1. ✅ **Custom Domain** (Optional)
   - Add your own domain name in Render settings
   - Update DNS records as instructed

2. ✅ **Auto-Deploy** (Already enabled)
   - Every push to `main` branch auto-deploys
   - Disable in settings if needed

3. ✅ **Backups** (Recommended)
   - Configure automatic database backups
   - Available in paid plans

4. ✅ **Monitoring** (Optional)
   - Set up alerts for errors
   - Monitor performance metrics

---

## 📚 Additional Resources

- **Render Docs**: https://render.com/docs
- **Flask Deployment**: https://flask.palletsprojects.com/en/latest/deploying/
- **PostgreSQL Guide**: https://render.com/docs/databases
- **Support**: Check Render Community or contact support

---

## ✅ Deployment Checklist

Use this checklist as you go:

- [ ] Created Render account
- [ ] Created PostgreSQL database
- [ ] Saved Internal Database URL
- [ ] Created Web Service
- [ ] Connected GitHub repository
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `gunicorn app:app`
- [ ] Added SECRET_KEY environment variable
- [ ] Added DATABASE_URL environment variable
- [ ] Deployed successfully
- [ ] Tested login (admin123)
- [ ] Changed admin code
- [ ] Created project site
- [ ] Tested core functionality

---

**🎉 Congratulations!** Your Istrom Inventory Management System is now live on Render!

---

*Last Updated: Deployment Guide v1.0*
*For issues or questions, check the logs or Render documentation.*

