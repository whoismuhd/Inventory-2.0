# Python 3.13 Compatibility Fix

## Problem
Your build is failing because Render is using Python 3.13, but `psycopg2-binary` doesn't have pre-built wheels for Python 3.13 yet.

## Solution: Force Python 3.11

### Step 1: Verify runtime.txt
Make sure `runtime.txt` exists in your repo root with:
```
python-3.11.0
```

### Step 2: Set Environment Variable in Render
In your Render Web Service settings:

1. Go to **"Environment"** section
2. Add environment variable:
   - **Key**: `PYTHON_VERSION`
   - **Value**: `3.11.0`
3. Save

### Step 3: Alternative - Use psycopg (psycopg3)
If you want to use Python 3.13, you can switch to psycopg3:

In `requirements.txt`, replace:
```
psycopg2-binary==2.9.9
```

With:
```
psycopg[binary]==3.1.18
```

And update imports in your code (but this requires code changes).

**Recommended**: Stick with Python 3.11 + psycopg2-binary (no code changes needed)

### Step 4: Redeploy
After making changes, redeploy your service.

