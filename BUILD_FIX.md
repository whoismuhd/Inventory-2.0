# Build Failure Troubleshooting Guide

If your build is failing on Render, follow these steps:

## 🔍 Step 1: Check Build Logs

1. Go to your Render dashboard
2. Click on your Web Service
3. Go to **"Logs"** tab
4. Look for error messages in red
5. Copy the error message (we'll use it to diagnose)

## 🛠️ Common Build Errors & Fixes

### Error 1: "ModuleNotFoundError" or "No module named"

**Cause**: Missing dependency in requirements.txt

**Fix**: Add missing package to `requirements.txt`

**Example errors**:
- `ModuleNotFoundError: No module named 'flask'`
- `ModuleNotFoundError: No module named 'gunicorn'`
- `ModuleNotFoundError: No module named 'psycopg2'`

**Solution**: Already fixed in requirements.txt - if still failing, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Error 2: "Command 'pip' failed" or "pip not found"

**Cause**: Build command incorrect

**Fix**: Update Build Command in Render settings to:
```
python -m pip install --upgrade pip && pip install -r requirements.txt
```

### Error 3: Python Version Mismatch

**Cause**: Wrong Python version

**Fix**: 
1. Create `runtime.txt` file (already created) with: `python-3.11.0`
2. Or set `PYTHON_VERSION` environment variable to `3.11.0`

### Error 4: "Failed building wheel for psycopg2-binary"

**Cause**: Compilation error with PostgreSQL driver

**Fix**: Ensure you're using `psycopg2-binary` (not `psycopg2`) - already in requirements.txt

If still failing, try adding to requirements.txt:
```
psycopg2-binary==2.9.9
setuptools>=65.5.0
```

### Error 5: "ImportError" or "cannot import name"

**Cause**: Circular import or missing module

**Fix**: Check your import statements. All imports should work.

### Error 6: Build succeeds but app won't start

**Cause**: Start command issue or missing gunicorn

**Fix**: 
1. Verify Start Command: `gunicorn app:app`
2. Ensure gunicorn is in requirements.txt (already there)

## ✅ Correct Render Configuration

### Build Command:
```
python -m pip install --upgrade pip && pip install -r requirements.txt
```

### Start Command:
```
gunicorn app:app
```

### Environment Variables:
- `SECRET_KEY`: (random generated key)
- `DATABASE_URL`: (your PostgreSQL internal URL)
- `PYTHON_VERSION`: `3.11.0` (optional but recommended)

## 🔧 Debugging Steps

### 1. Verify Repository Structure

Make sure these files exist in your repo root:
- ✅ `app.py`
- ✅ `requirements.txt`
- ✅ `runtime.txt` (newly added)
- ✅ `database.py`
- ✅ `models.py`
- ✅ `routes.py`
- ✅ `utils.py`
- ✅ `templates/` folder
- ✅ `static/` folder

### 2. Test Locally First

Before deploying, test locally:
```bash
pip install -r requirements.txt
python app.py
```

### 3. Check Build Command Output

In Render logs, look for:
- ✅ `Successfully installed ...`
- ✅ `Collecting ...`
- ❌ Any red error messages

### 4. Verify Requirements.txt Format

Requirements.txt should have NO blank lines at the end:
```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
...
psycopg2-binary==2.9.9
```

(No extra blank line after last package)

## 🚨 Specific Error Messages

### "ERROR: Failed building wheel"
**Solution**: Add `setuptools>=65.5.0` to requirements.txt (already done)

### "ERROR: Could not find a version that satisfies"
**Solution**: Check package names and versions are correct

### "ERROR: Command errored out"
**Solution**: Check Python version compatibility

### "ModuleNotFoundError: No module named 'app'"
**Solution**: Verify you're in the root directory and `app.py` exists

### "gunicorn: command not found"
**Solution**: Verify gunicorn is in requirements.txt (already there)

## 📝 Updated Build Configuration

I've made these updates to fix common issues:

1. ✅ Added `runtime.txt` to specify Python 3.11.0
2. ✅ Added `setuptools` to requirements.txt
3. ✅ Verified all dependencies are present

## 🔄 Next Steps After Fix

1. **Commit and push changes**:
   ```bash
   git add runtime.txt requirements.txt BUILD_FIX.md
   git commit -m "Fix build configuration for Render"
   git push origin main
   ```

2. **Update Render Build Command** (if needed):
   ```
   python -m pip install --upgrade pip && pip install -r requirements.txt
   ```

3. **Redeploy**:
   - Render will auto-deploy on push
   - Or manually trigger deployment in Render dashboard

## 💡 Still Failing?

1. **Check exact error message** from Render logs
2. **Share the error** - it will help identify the specific issue
3. **Verify**:
   - Repository is connected correctly
   - Branch is set to `main`
   - All files are committed and pushed
   - Build command is exactly as shown above

## 📞 Common Render Build Issues

- **Slow builds**: Normal for first deployment (5-10 minutes)
- **Timeout errors**: Try simplifying build command
- **Memory errors**: Upgrade to paid plan (more resources)
- **Network errors**: Retry deployment (Render infrastructure issue)

---

**Need specific help?** Share the exact error message from Render logs and I can provide targeted fixes!

