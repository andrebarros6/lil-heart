# Streamlit Cloud Deployment Guide

## Quick Start

### 1. Deploy to Streamlit Cloud

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Select your repository and branch
5. Set main file path: `app.py`
6. Click "Deploy"

### 2. Configure Secrets

Once your app is deployed, configure the required secrets:

1. Go to your app dashboard on Streamlit Cloud
2. Click **Settings** (⚙️) → **Secrets**
3. Add the following secrets in TOML format:

```toml
# Supabase Configuration (Required)
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_ANON_KEY = "your-anon-key-here"

# Base URL for Share Links (Required for family sharing)
BASE_URL = "https://your-app-name.streamlit.app"
```

**Important Notes:**
- Replace `your-project.supabase.co` with your actual Supabase project URL
- Replace `your-anon-key-here` with your Supabase anon/public key
- Replace `your-app-name.streamlit.app` with your actual Streamlit Cloud URL
  - Find this in your browser's address bar when viewing your app
  - Don't include trailing slashes
  - Example: `https://lil-heart.streamlit.app`

4. Click **Save**
5. Your app will automatically restart with the new configuration

### 3. Find Your App URL

Your Streamlit Cloud URL follows this pattern:
```
https://your-app-name.streamlit.app
```

or

```
https://share.streamlit.io/your-username/your-repo/main/app.py
```

**To find it:**
1. Open your deployed app in a browser
2. Look at the address bar
3. Copy everything before the `?` (if there's a query string)

### 4. Test Family Sharing

Once `BASE_URL` is configured:

1. Log in to your app
2. Go to **🔗 Sharing** page
3. Generate a share link
4. You should see a full URL like: `https://your-app.streamlit.app/?share_token=abc-123`
5. Share this link with family members

## Troubleshooting

### Share links show localhost URL

**Problem:** Generated share links show `http://localhost:8501/?share_token=...`

**Solution:** Add `BASE_URL` to your Streamlit Cloud secrets (see step 2 above)

### Environment variables not found

**Problem:** Login fails with "Supabase credentials not found"

**Solution:**
1. Check that secrets are configured in Streamlit Cloud (not local `.env`)
2. Verify TOML syntax is correct (no quotes around keys, values in quotes)
3. Restart the app after adding secrets

### App won't start

**Problem:** App shows installation errors

**Solution:**
1. Check that `requirements.txt`, `packages.txt`, and `runtime.txt` are present
2. Verify Python version in `runtime.txt` is supported (3.9-3.12)
3. Check deployment logs for specific errors

## Local Development

For local development, continue using `.env` file:

```bash
# .env (local only, never commit!)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
BASE_URL=http://localhost:8501
```

The app automatically detects whether it's running locally (uses `.env`) or on Streamlit Cloud (uses Secrets).

## Security Best Practices

1. **Never commit `.env` to git** (already in `.gitignore`)
2. **Use Streamlit Cloud Secrets** for all sensitive configuration
3. **Enable password protection** on share links for sensitive photos
4. **Regularly revoke and regenerate** share links if they're accidentally leaked
5. **Use Row Level Security** in Supabase to protect data (already configured)

## Need Help?

- [Streamlit Cloud Documentation](https://docs.streamlit.io/streamlit-community-cloud)
- [Supabase Documentation](https://supabase.com/docs)
- Project README.md for detailed setup instructions
