# Clinton Tech Dev Suite

A production-ready Flask CMS for web developers building static client websites. Full admin panel at `/admin` with live theme switching, 30+ colour schemes, and complete content management.

---

## Features

- **22 visual themes** — Minimal Edge, Bold Studio, Neon Future, Luxury Gold, Brutalist, Magazine, and more
- **30 colour schemes** — independently swappable, applied via CSS variables
- **7 button styles** — Solid, Outline, Ghost, Rounded, Shadow, Gradient, Underline
- **Admin panel at `/admin`** — password protected, no public access
- **Full CMS** — edit all text, upload images, manage pages and sections
- **Scroll animations** — fade, stagger, zoom (toggleable)
- **Font Awesome 6** icons throughout (no emojis)
- **Production ready** — Render.com + PostgreSQL or SQLite local dev

---

## Local Development

### 1. Clone and set up

```bash
git clone <your-repo>
cd clinton-tech-suite
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set environment variables (optional for local)

```bash
export SECRET_KEY="your-secret-key"
export ADMIN_USERNAME="admin"
export ADMIN_PASSWORD="your-password"
# DATABASE_URL defaults to SQLite if not set
```

### 3. Initialise database

```bash
python init_db.py
```

### 4. Run development server

```bash
python app.py
```

Visit:
- **Site:** http://localhost:5000
- **Admin:** http://localhost:5000/admin

Default login: `admin` / `clinton2024`

---

## Deploying to Render.com

### Option A — Using render.yaml (recommended)

1. Push this project to a GitHub repository
2. Go to [render.com](https://render.com) → New → Blueprint
3. Connect your GitHub repo
4. Render reads `render.yaml` and creates the web service + PostgreSQL database automatically
5. In the Render dashboard → Environment, set:
   - `ADMIN_PASSWORD` to a strong password
6. Deploy. Done.

### Option B — Manual setup

1. **Create PostgreSQL database** on Render (free tier)
   - Copy the **Internal Database URL**

2. **Create Web Service** on Render
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT`

3. **Set Environment Variables** in Render dashboard:
   | Key | Value |
   |-----|-------|
   | `DATABASE_URL` | (paste from PostgreSQL Internal URL) |
   | `SECRET_KEY` | any long random string |
   | `ADMIN_USERNAME` | admin |
   | `ADMIN_PASSWORD` | your-strong-password |

4. **Initialise the database** — in Render Shell tab, run:
   ```bash
   python init_db.py
   ```

5. Visit your Render URL → `/admin` to log in

---

## Admin Panel Guide

### Accessing Admin
- URL: `yourdomain.com/admin`
- Only accessible with your credentials — no link shown on public site

### Changing Theme
1. Admin → Site Settings → scroll to **Theme**
2. Click any of the 22 theme cards
3. Save Settings — changes apply instantly site-wide

### Changing Colour Scheme
1. Admin → Site Settings → scroll to **Color Scheme**
2. Click any of the 30 colour swatches
3. Save Settings

### Editing Page Content
1. Admin → Pages → click **Edit** on any page
2. Each section has editable Heading, Subheading, Content (rich text), Button, and Image
3. Toggle sections on/off with the **Visible** checkbox
4. Click **Save Section**

### Adding a New Page
1. Admin → Pages → **New Page**
2. Enter title (slug auto-generates)
3. After creation, add sections from the Edit Page view

### Button Style
1. Admin → Site Settings → scroll to **Button Style**
2. Choose from 7 presets
3. Adjust border radius with the slider (0–50px)
4. Save Settings

### Animations
- Admin → Site Settings → toggle **Scroll Animations** on/off
- Uses CSS transforms only (GPU accelerated, respects `prefers-reduced-motion`)

### Managing CTAs / Initiatives
- Admin → Initiatives / CTAs
- Add, edit, delete service cards shown on homepage
- Each card has title, description, Font Awesome icon, button text/link

### Social Links
- Admin → Social Links
- Use the quick-pick buttons for common platforms
- Icons use Font Awesome Brand classes (e.g. `fa-brands fa-github`)

### Maintenance Mode
- Admin → Site Settings → toggle **Maintenance Mode**
- Visitors see a maintenance page; admin still works normally

---

## Developer Guide

### Adding a New Theme

In `app.py`, find the `get_theme_css()` function and add a new entry:

```python
"my-theme-id": """
    --font-heading: 'YourFont', sans-serif;
    --font-body: 'YourFont', sans-serif;
    --radius: 8px;
    --shadow: 0 4px 20px rgba(0,0,0,0.1);
    --section-padding: 100px 0;
""",
```

Then add to the `THEMES` list:

```python
{"id": "my-theme-id", "name": "My Theme", "desc": "Theme description"},
```

Load any Google Font by adding it to the `<link>` tag in `templates/site/base.html`.

### Adding a New Colour Scheme

In `app.py`, add to the `COLOR_SCHEMES` list:

```python
{
    "id": "my-scheme",
    "name": "My Scheme",
    "primary": "#FF6600",
    "secondary": "#CC4400",
    "accent": "#FF9944",
    "bg": "#0a0505",
    "text": "#f5f0ee"
},
```

### Adding a New Section Type

1. Add rendering logic in `templates/site/index.html` inside the `{% for sec in sections %}` loop:

```html
{% elif sec.type == 'mytype' %}
<section id="mytype">
    <div class="container">
        <h2>{{ sec.heading }}</h2>
        <!-- your layout -->
    </div>
</section>
```

2. Add the type option in `templates/admin/edit_page.html` in the "Add Section" grid.

### File Upload Location
Uploads stored in `static/uploads/`. On Render, use persistent disk or external storage (S3/Cloudflare R2) for production — Render's ephemeral filesystem resets on deploy.

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `clinton-tech-dev-suite-secret-2024` | Flask session secret — change in production |
| `ADMIN_USERNAME` | `admin` | Admin login username |
| `ADMIN_PASSWORD` | `clinton2024` | Admin login password — **always change** |
| `DATABASE_URL` | `sqlite:///clinton.db` | Database URL. Use PostgreSQL URL for Render |

---

## Project Structure

```
clinton-tech-suite/
├── app.py              # Main Flask app, routes, theme/scheme data
├── database.py         # SQLAlchemy models
├── init_db.py          # One-time DB seeder
├── requirements.txt    # Python dependencies
├── render.yaml         # Render.com deployment config
├── static/
│   └── uploads/        # Uploaded logos, images, favicons
└── templates/
    ├── site/
    │   ├── base.html       # Frontend base (themes, colours, animations)
    │   ├── index.html      # Homepage with all section types
    │   ├── page.html       # Generic page template
    │   └── maintenance.html
    └── admin/
        ├── base.html       # Admin sidebar layout
        ├── login.html
        ├── dashboard.html
        ├── settings.html   # Theme/colour/button pickers
        ├── pages.html
        ├── edit_page.html  # Section editor with Quill rich text
        ├── new_page.html
        ├── nav.html
        ├── socials.html
        └── initiatives.html
```
