# Render.com Deployment Guide — Clinton Tech Dev Suite

Complete step-by-step instructions to get your site live on Render.com.

---

## What You Need

- A [Render.com](https://render.com) account (free tier works)
- A [GitHub](https://github.com) account
- Your project files (this ZIP, extracted)

---

## Step 1 — Push to GitHub

### 1a. Create a new GitHub repository

1. Go to https://github.com/new
2. Name it: `clinton-tech-dev-suite`
3. Set to **Private** (recommended)
4. Do NOT initialise with README (you already have files)
5. Click **Create repository**

### 1b. Upload your files

**Option A — GitHub website (easiest):**
1. On your new repo page, click **uploading an existing file**
2. Drag and drop ALL files from the extracted ZIP folder
3. Make sure the folder structure is maintained:
   - `app.py` at root level
   - `database.py` at root level
   - `templates/` folder
   - `static/` folder
   - etc.
4. Click **Commit changes**

**Option B — Git command line:**
```bash
cd clinton-tech-suite          # your extracted folder
git init
git add .
git commit -m "Initial deploy"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/clinton-tech-dev-suite.git
git push -u origin main
```

---

## Step 2 — Create a PostgreSQL Database on Render

1. Log in to [render.com](https://render.com)
2. Click **New +** in the top right
3. Select **PostgreSQL**
4. Fill in:
   - **Name:** `clinton-db`
   - **Region:** Choose closest to you (e.g. Oregon, Frankfurt)
   - **Plan:** Free
5. Click **Create Database**
6. Wait ~1 minute for it to provision
7. On the database page, find **Connections** section
8. Copy the **Internal Database URL** — looks like:
   ```
   postgresql://clinton_db_user:XXXX@dpg-XXXX-a/clinton_db
   ```
   Keep this — you'll need it in Step 3.

---

## Step 3 — Create the Web Service

1. Click **New +** again
2. Select **Web Service**
3. Select **Build and deploy from a Git repository**
4. Click **Connect** next to your `clinton-tech-dev-suite` repo
5. Fill in the settings:

| Field | Value |
|-------|-------|
| **Name** | `clinton-tech-dev-suite` |
| **Region** | Same as your database |
| **Branch** | `main` |
| **Root Directory** | *(leave blank)* |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120` |
| **Plan** | Free |

---

## Step 4 — Set Environment Variables

Still on the Web Service creation page, scroll down to **Environment Variables**.

Click **Add Environment Variable** for each of the following:

| Key | Value | Notes |
|-----|-------|-------|
| `DATABASE_URL` | *(paste Internal DB URL from Step 2)* | Required for PostgreSQL |
| `SECRET_KEY` | `any-long-random-string-here-abc123xyz` | Change to something random |
| `ADMIN_USERNAME` | `admin` | Your admin login username |
| `ADMIN_PASSWORD` | `YourStrongPassword123!` | **Change this — never use default** |

> **Tip:** For SECRET_KEY, use something like: `clinton-prod-2024-xK9mP2qL8wN5jR3v`

Click **Create Web Service**.

---

## Step 5 — Wait for First Deploy

1. Render will now install dependencies and start your app
2. Watch the **Logs** tab — takes 2–4 minutes
3. You'll see: `Booting worker with pid` when it's ready
4. A green **Live** badge appears at the top

If you see errors, check Step 6 (Troubleshooting) below.

---

## Step 6 — Initialise the Database

This is a **one-time step** to create tables and seed default content.

1. On your Web Service page, click the **Shell** tab (top navigation)
2. Wait for the shell to connect
3. Type this command and press Enter:

```bash
python init_db.py
```

You should see:
```
Initialising database...
Seeding default content...
Done! Default admin login:
  URL:      https://your-app.onrender.com/admin
  Username: admin
  Password: (whatever you set in Step 4)
```

---

## Step 7 — Visit Your Live Site

1. At the top of the Web Service page, click your `.onrender.com` URL
2. Your site is live!
3. Go to `https://your-app.onrender.com/admin` to log in

---

## Step 8 — Add a Custom Domain (Optional)

1. On your Web Service page, click **Settings**
2. Scroll to **Custom Domains**
3. Click **Add Custom Domain**
4. Enter your domain (e.g. `clintontech.dev`)
5. Render gives you a CNAME record to add to your DNS provider
6. Add the CNAME in your domain registrar (GoDaddy, Namecheap, Cloudflare, etc.)
7. Wait for DNS propagation (up to 48 hours, usually under 1 hour)
8. Render auto-provisions a free SSL certificate

---

## Important Notes for Free Tier

- **Sleep after inactivity:** Free web services sleep after 15 minutes of no traffic. First request after sleep takes ~30 seconds. Upgrade to Starter ($7/mo) to keep it always-on.
- **Storage:** Uploaded images (logos, section images) are stored locally. On Render free tier, the filesystem resets on each deploy. For persistent uploads, see the "Persistent Uploads" section below.
- **Database:** Free PostgreSQL databases expire after 90 days on Render. Back up your data before then, or upgrade to a paid plan.

---

## Persistent Image Uploads (Recommended for Production)

Since Render's free tier has ephemeral storage, uploaded images are lost on redeploy.

**Solution: Use Cloudflare R2 or AWS S3**

For now, the simplest workaround is to re-upload your logo and images after each deploy, or upgrade to Render's paid plan which includes a persistent disk.

To add a persistent disk on Render:
1. Web Service → **Settings** → **Disks**
2. Add Disk:
   - **Name:** `uploads`
   - **Mount Path:** `/opt/render/project/src/static/uploads`
   - **Size:** 1 GB (minimum)
3. Costs $0.25/GB/month

---

## Redeploying After Code Changes

Render auto-deploys whenever you push to your GitHub `main` branch.

```bash
# Make your changes locally, then:
git add .
git commit -m "Update site content"
git push origin main
# Render detects the push and redeploys automatically
```

---

## Troubleshooting

### "Application failed to respond"
- Check the **Logs** tab for Python errors
- Make sure all environment variables are set correctly
- Confirm Build Command and Start Command match Step 3 exactly

### "No such table" errors
- You need to run `python init_db.py` in the Shell tab (Step 6)

### Admin login not working
- Double-check `ADMIN_USERNAME` and `ADMIN_PASSWORD` in Environment Variables
- Values are case-sensitive

### Database connection errors
- Make sure `DATABASE_URL` is the **Internal** URL (not External)
- Both database and web service must be in the same Render region

### Images not showing after redeploy
- This is the ephemeral filesystem issue — see "Persistent Image Uploads" above

### Build failing
- Check that `requirements.txt` is at the root of your repo
- Ensure `app.py` and `database.py` are at the root (not inside a subfolder)

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes (production) | SQLite locally | PostgreSQL connection string from Render |
| `SECRET_KEY` | Yes | insecure default | Flask session encryption key |
| `ADMIN_USERNAME` | No | `admin` | Admin panel login username |
| `ADMIN_PASSWORD` | **Yes** | `clinton2024` | Admin panel login password — always change |

---

## Quick Checklist

- [ ] Files pushed to GitHub
- [ ] PostgreSQL database created on Render
- [ ] Web Service created with correct Build + Start commands
- [ ] All 4 environment variables set
- [ ] First deploy succeeded (green Live badge)
- [ ] `python init_db.py` run in Shell tab
- [ ] Admin login tested at `/admin`
- [ ] Custom domain added (optional)

---

*Clinton Tech Dev Suite — Built for developers, by a developer.*
