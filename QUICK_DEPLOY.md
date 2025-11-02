# Quick Deploy Checklist for Render

## Your Database Connection
Your PostgreSQL database is ready:
- **Internal URL**: `postgresql://istrompostgre_zgkc_user:X7tmMF5MDpxAPAAhaGFuiZs6q3EeIxDd@dpg-d43q673ipnbc73c7fjlg-a/istrompostgre_zgkc`

## Render Deployment Steps

### 1. Create Web Service on Render

1. Go to https://dashboard.render.com
2. Click **"New +"** → **"Web Service"**
3. Connect GitHub repository:
   - Click **"Connect account"** if not already connected
   - Select repository: **`whoismuhd/Inventory-2.0`**
   - Click **"Connect"**

### 2. Configure Service

Fill in these settings:

- **Name**: `istrom-inventory` (or any name you prefer)
- **Region**: Choose closest to you
- **Branch**: `main`
- **Root Directory**: Leave empty
- **Runtime**: `Python 3`
- **Build Command**: 
  ```
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```
  gunicorn app:app
  ```
- **Plan**: Choose Free (for testing) or Paid (for production)

### 3. Environment Variables

Click **"Advanced"** → **"Add Environment Variable"** and add:

1. **SECRET_KEY**
   - Click **"Generate"** or generate manually:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   - This should be a long random string (keep it secret!)

2. **DATABASE_URL** (IMPORTANT: Use Internal URL)
   - Value: 
   ```
   postgresql://istrompostgre_zgkc_user:X7tmMF5MDpxAPAAhaGFuiZs6q3EeIxDd@dpg-d43q673ipnbc73c7fjlg-a/istrompostgre_zgkc
   ```
   - ⚠️ Make sure this is the **INTERNAL** Database URL from your PostgreSQL service

3. (Optional) **PYTHON_VERSION**
   - Value: `3.11.0`

### 4. Link Database (Alternative Method)

Instead of manually setting DATABASE_URL, you can:

1. In your Web Service settings, scroll to **"Links"** section
2. Click **"Link Resource"**
3. Select your PostgreSQL database
4. This automatically sets `DATABASE_URL` for you

### 5. Deploy

1. Click **"Create Web Service"**
2. Render will:
   - Clone your repository
   - Install dependencies
   - Build your application
   - Start the server
3. Monitor the **"Logs"** tab for progress
4. Once deployed, your app URL will be: `https://your-service-name.onrender.com`

### 6. First Login

1. Visit your deployed URL
2. Login with default admin code: **`admin123`**
3. **IMMEDIATELY** change the admin code via Admin Settings!
4. Create your first project site
5. Set up access codes

## Troubleshooting

### Build Fails
- Check logs for missing dependencies
- Verify `requirements.txt` is correct
- Ensure Python version is compatible

### Database Connection Error
- Verify `DATABASE_URL` is set correctly
- Ensure you're using **INTERNAL** URL (not external)
- Check that database service is running
- URL should start with `postgresql://` (not `postgres://`)

### Application Won't Start
- Check that gunicorn is installed (should be in requirements.txt)
- Verify start command: `gunicorn app:app`
- Check application logs for errors

### 502 Bad Gateway
- Wait a few minutes (free tier services spin up on first request)
- Check logs for errors
- Verify database connection

## Security Reminders

- ✅ Change default admin code (`admin123`) immediately
- ✅ Use strong SECRET_KEY (32+ random characters)
- ✅ Never commit secrets to GitHub
- ✅ Enable automatic HTTPS (done by default on Render)

## Free Tier Notes

- ⏰ Services spin down after 15 minutes of inactivity
- 🐌 First request may take 30-60 seconds to wake up
- 💾 Database has 90-day data retention
- 📊 Limited resources (upgrade for production)

## Next Steps After Deployment

1. Test all functionality
2. Create project sites
3. Set up access codes
4. Migrate any existing data (if needed)
5. Set up custom domain (optional)
6. Configure backups (recommended for production)

---

**Need Help?** Check the full [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

