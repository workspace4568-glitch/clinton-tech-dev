"""
Clinton Tech Dev Suite — Flask Application
Routes for the site frontend and admin panel.
"""
import os, re, json, shutil, tempfile
from datetime import datetime
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, send_file, abort, jsonify)
from werkzeug.utils import secure_filename
from database import (
    db, init_db, get_settings, get_pages, get_page_by_slug, get_page_by_id,
    get_home_page, get_sections, get_nav, get_socials, get_initiatives,
    get_all_initiatives, get_service_cards, get_all_service_cards,
    get_portfolio_items, get_all_portfolio_items,
    get_gallery_items, get_all_gallery_items, get_gallery_categories,
    init_gallery, init_service_cards, init_portfolio_items, USE_POSTGRES, _p
)
from exporter import export_static, zip_export

# ── App Setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'clinton-tech-dev-secret-2024')

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_IMAGE = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'ico'}
ALLOWED_MEDIA = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg', 'mp4', 'webm', 'mov', 'avi'}

def allowed_image(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE

def allowed_media(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_MEDIA

def save_upload(file, folder=None):
    """Save an uploaded file and return its filename."""
    if not file or file.filename == '':
        return None
    fname = secure_filename(file.filename)
    # Prefix with timestamp to avoid collisions
    base, ext = os.path.splitext(fname)
    fname = f"{base}_{int(datetime.now().timestamp())}{ext}"
    dest = os.path.join(folder or UPLOAD_FOLDER, fname)
    file.save(dest)
    return fname

# ── Themes & Schemes ──────────────────────────────────────────────────────────

THEMES = [
    {'id': 'bold-studio',   'name': 'Bold Studio',    'desc': 'Dark, high-contrast agency feel'},
    {'id': 'minimal-light', 'name': 'Minimal Light',  'desc': 'Clean white canvas, lots of space'},
    {'id': 'neon-dark',     'name': 'Neon Dark',      'desc': 'Cyberpunk glow on deep black'},
    {'id': 'gold-luxury',   'name': 'Gold Luxury',    'desc': 'Premium gold on near-black'},
    {'id': 'pastel-soft',   'name': 'Pastel Soft',    'desc': 'Gentle, friendly tones'},
    {'id': 'retro-green',   'name': 'Retro Terminal', 'desc': 'Old-school green-on-black terminal'},
    {'id': 'organic-earth', 'name': 'Organic Earth',  'desc': 'Nature-inspired greens and browns'},
    {'id': 'sunset-warm',   'name': 'Sunset Warm',    'desc': 'Coral and golden warm palette'},
    {'id': 'cinematic',     'name': 'Cinematic',      'desc': 'Deep navy, dramatic shadows'},
    {'id': 'glassmorphism', 'name': 'Glassmorphism',  'desc': 'Frosted glass effects'},
]

COLOR_SCHEMES = [
    {'id': 'crimson-dark',  'name': 'Crimson Dark',  'primary': '#DC143C', 'secondary': '#a00f2b', 'accent': '#FF4D6D', 'bg': '#0a0a0a', 'text': '#e8e8e8'},
    {'id': 'cobalt-dark',   'name': 'Cobalt Dark',   'primary': '#0077B6', 'secondary': '#005f99', 'accent': '#00B4D8', 'bg': '#090e1a', 'text': '#e0eaf8'},
    {'id': 'violet-dark',   'name': 'Violet Dark',   'primary': '#7C3AED', 'secondary': '#5b21b6', 'accent': '#A78BFA', 'bg': '#0d0a1e', 'text': '#ede9fe'},
    {'id': 'emerald-dark',  'name': 'Emerald Dark',  'primary': '#059669', 'secondary': '#047857', 'accent': '#34D399', 'bg': '#071a12', 'text': '#d1fae5'},
    {'id': 'amber-dark',    'name': 'Amber Dark',    'primary': '#D97706', 'secondary': '#b45309', 'accent': '#FCD34D', 'bg': '#110900', 'text': '#fef3c7'},
    {'id': 'rose-light',    'name': 'Rose Light',    'primary': '#E11D48', 'secondary': '#be123c', 'accent': '#FB7185', 'bg': '#fff1f2', 'text': '#1a0a0d'},
    {'id': 'sky-light',     'name': 'Sky Light',     'primary': '#0284C7', 'secondary': '#0369a1', 'accent': '#38BDF8', 'bg': '#f0f9ff', 'text': '#0c1a26'},
    {'id': 'forest-light',  'name': 'Forest Light',  'primary': '#16A34A', 'secondary': '#15803d', 'accent': '#4ADE80', 'bg': '#f0fdf4', 'text': '#052e16'},
    {'id': 'gold-black',    'name': 'Gold & Black',  'primary': '#C9A84C', 'secondary': '#a07c2e', 'accent': '#FFD700', 'bg': '#0a0800', 'text': '#f5e6c8'},
    {'id': 'mono-dark',     'name': 'Mono Dark',     'primary': '#e8e8e8', 'secondary': '#aaaaaa', 'accent': '#ffffff', 'bg': '#0a0a0a', 'text': '#e8e8e8'},
]

THEME_CSS_MAP = {
    'bold-studio':   '--radius:6px; --shadow:0 8px 32px rgba(0,0,0,0.45);',
    'minimal-light': '--radius:4px; --shadow:0 2px 12px rgba(0,0,0,0.08); --section-padding:80px 0;',
    'neon-dark':     '--radius:2px; --shadow:0 0 20px var(--primary)66; --section-padding:90px 0;',
    'gold-luxury':   '--radius:0px; --shadow:0 4px 40px rgba(0,0,0,0.6);',
    'pastel-soft':   '--radius:16px; --shadow:0 4px 20px rgba(0,0,0,0.06);',
    'retro-green':   '--radius:0px; --shadow:0 0 10px #00FF0033;',
    'organic-earth': '--radius:12px; --shadow:0 6px 24px rgba(0,0,0,0.15);',
    'sunset-warm':   '--radius:8px; --shadow:0 8px 28px rgba(255,107,107,0.2);',
    'cinematic':     '--radius:4px; --shadow:0 16px 48px rgba(0,0,0,0.7);',
    'glassmorphism': '--radius:16px; --shadow:0 8px 32px rgba(0,0,0,0.3);',
}

def get_scheme(scheme_id):
    for s in COLOR_SCHEMES:
        if s['id'] == scheme_id:
            return s
    return COLOR_SCHEMES[0]

def get_theme_css(theme_id):
    return THEME_CSS_MAP.get(theme_id, '')

def site_context():
    """Build common context dict for all site (frontend) pages."""
    with db() as conn:
        s  = get_settings(conn)
        nav    = get_nav(conn)
        socials= get_socials(conn)
    scheme   = get_scheme(s.get('color_scheme', 'crimson-dark'))
    theme_css= get_theme_css(s.get('theme', 'bold-studio'))
    return dict(s=s, nav=nav, socials=socials, scheme=scheme, theme_css=theme_css)

# ── Login required decorator ──────────────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin'):
            return redirect('/admin/login')
        return f(*args, **kwargs)
    return decorated

def admin_context():
    """Common context for admin pages."""
    with db() as conn:
        s = get_settings(conn)
    return dict(s=s, themes=THEMES, schemes=COLOR_SCHEMES)

# ── Init DB on startup ────────────────────────────────────────────────────────

with app.app_context():
    try:
        init_db()
        with db() as conn:
            init_service_cards(conn)
            init_portfolio_items(conn)
            init_gallery(conn)
    except Exception as e:
        print(f"DB init warning: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# SITE (FRONTEND) ROUTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/')
def index():
    with db() as conn:
        s        = get_settings(conn)
        if s.get('maintenance_mode'):
            return render_template('site/maintenance.html', s=s)
        home     = get_home_page(conn)
        sections = get_sections(conn, home['id'], enabled_only=True) if home else []
        services = get_service_cards(conn, enabled_only=True)
        portfolio= get_portfolio_items(conn, enabled_only=True)
        inits    = get_initiatives(conn)
        nav      = get_nav(conn)
        socials  = get_socials(conn)

    scheme    = get_scheme(s.get('color_scheme', 'crimson-dark'))
    theme_css = get_theme_css(s.get('theme', 'bold-studio'))
    return render_template('site/index.html',
        s=s, nav=nav, socials=socials, scheme=scheme, theme_css=theme_css,
        sections=sections, services=services, portfolio=portfolio, initiatives=inits)


@app.route('/page/<slug>')
def site_page(slug):
    with db() as conn:
        s    = get_settings(conn)
        if s.get('maintenance_mode'):
            return render_template('site/maintenance.html', s=s)
        page = get_page_by_slug(conn, slug)
        if not page or not page.get('visible'):
            abort(404)
        sections = get_sections(conn, page['id'], enabled_only=True)
        nav     = get_nav(conn)
        socials = get_socials(conn)

    scheme    = get_scheme(s.get('color_scheme', 'crimson-dark'))
    theme_css = get_theme_css(s.get('theme', 'bold-studio'))
    return render_template('site/page.html',
        s=s, nav=nav, socials=socials, scheme=scheme, theme_css=theme_css,
        page=page, sections=sections)


@app.route('/gallery')
def gallery():
    cat = request.args.get('cat', 'All')
    with db() as conn:
        s       = get_settings(conn)
        if s.get('maintenance_mode'):
            return render_template('site/maintenance.html', s=s)
        items   = get_gallery_items(conn, category=cat if cat != 'All' else None, enabled_only=True)
        cats    = ['All'] + get_gallery_categories(conn)
        nav     = get_nav(conn)
        socials = get_socials(conn)

    scheme    = get_scheme(s.get('color_scheme', 'crimson-dark'))
    theme_css = get_theme_css(s.get('theme', 'bold-studio'))
    return render_template('site/gallery.html',
        s=s, nav=nav, socials=socials, scheme=scheme, theme_css=theme_css,
        items=items, cats=cats, active_cat=cat)


@app.errorhandler(404)
def not_found(e):
    ctx = site_context()
    return render_template('site/404.html', **ctx), 404

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — AUTH
# ══════════════════════════════════════════════════════════════════════════════

ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'clinton2024')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        pw = request.form.get('password', '')
        if pw == ADMIN_PASSWORD:
            session['admin'] = True
            session.permanent = True
            return redirect('/admin/dashboard')
        flash('Incorrect password.', 'error')
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin/login')


@app.route('/admin')
def admin_root():
    return redirect('/admin/dashboard')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    with db() as conn:
        s      = get_settings(conn)
        pages  = get_pages(conn)
    return render_template('admin/dashboard.html',
        s=s, pages=pages, themes=THEMES, schemes=COLOR_SCHEMES)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — SETTINGS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    with db() as conn:
        s = get_settings(conn)
        if request.method == 'POST':
            f = request.form

            # Handle file uploads
            logo_url    = s.get('logo_url', '')
            favicon_url = s.get('favicon_url', '')
            logo_file    = request.files.get('logo')
            favicon_file = request.files.get('favicon')
            if logo_file and logo_file.filename and allowed_image(logo_file.filename):
                logo_url = save_upload(logo_file)
            if favicon_file and favicon_file.filename and allowed_image(favicon_file.filename):
                favicon_url = save_upload(favicon_file)

            fields = {
                'site_name':              f.get('site_name', ''),
                'tagline':                f.get('tagline', ''),
                'logo_url':               logo_url,
                'favicon_url':            favicon_url,
                'footer_text':            f.get('footer_text', ''),
                'contact_email':          f.get('contact_email', ''),
                'contact_phone':          f.get('contact_phone', ''),
                'contact_address':        f.get('contact_address', ''),
                'contact_hours':          f.get('contact_hours', ''),
                'meta_title':             f.get('meta_title', ''),
                'meta_description':       f.get('meta_description', ''),
                'theme':                  f.get('theme', 'bold-studio'),
                'color_scheme':           f.get('color_scheme', 'crimson-dark'),
                'font_heading':           f.get('font_heading', ''),
                'font_body':              f.get('font_body', ''),
                'font_mono':              f.get('font_mono', ''),
                'container_max_width':    int(f.get('container_max_width', 1200)),
                'container_justify':      f.get('container_justify', 'center'),
                'hero_position':          f.get('hero_position', 'sticky'),
                'hero_height':            f.get('hero_height', 'screen'),
                'nav_style':              f.get('nav_style', 'slide-right'),
                'button_style':           f.get('button_style', 'filled'),
                'button_radius':          int(f.get('button_radius', 6)),
                'animations_enabled':     1 if f.get('animations_enabled') else 0,
                'announcement_bar_enabled': 1 if f.get('announcement_bar_enabled') else 0,
                'announcement_text':      f.get('announcement_text', ''),
                'announcement_link':      f.get('announcement_link', ''),
                'maintenance_mode':       1 if f.get('maintenance_mode') else 0,
                'maintenance_message':    f.get('maintenance_message', 'We\'ll be back soon.'),
            }

            p = _p()
            cur = conn.cursor()
            for key, val in fields.items():
                cur.execute(
                    f"UPDATE settings SET value={p} WHERE key={p}",
                    (str(val), key)
                )
                if cur.rowcount == 0:
                    cur.execute(
                        f"INSERT INTO settings (key, value) VALUES ({p}, {p})",
                        (key, str(val))
                    )

            flash('Settings saved!', 'success')
            return redirect('/admin/settings')

    return render_template('admin/settings.html',
        s=s, themes=THEMES, schemes=COLOR_SCHEMES)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — PAGES
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/pages')
@login_required
def admin_pages():
    with db() as conn:
        s     = get_settings(conn)
        pages = get_pages(conn)
    return render_template('admin/pages.html', s=s, pages=pages)


@app.route('/admin/pages/new', methods=['GET', 'POST'])
@login_required
def admin_pages_new():
    with db() as conn:
        s = get_settings(conn)
        if request.method == 'POST':
            title = request.form.get('title', '').strip()
            slug  = request.form.get('slug', '').strip().lower()
            slug  = re.sub(r'[^a-z0-9\-]', '', slug)
            p = _p()
            conn.cursor().execute(
                f"INSERT INTO pages (title, slug, visible) VALUES ({p},{p},1)",
                (title, slug)
            )
            flash(f'Page "{title}" created.', 'success')
            return redirect('/admin/pages')
    return render_template('admin/new_page.html', s=s)


@app.route('/admin/pages/<int:page_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_page(page_id):
    with db() as conn:
        s    = get_settings(conn)
        page = get_page_by_id(conn, page_id)
        if not page:
            abort(404)

        if request.method == 'POST':
            f   = request.form
            p   = _p()
            cur = conn.cursor()
            cur.execute(
                f"UPDATE pages SET title={p}, slug={p}, visible={p} WHERE id={p}",
                (f.get('title',''), f.get('slug',''),
                 1 if f.get('visible') else 0, page_id)
            )
            flash('Page updated.', 'success')
            return redirect(f'/admin/pages/{page_id}')

        sections = get_sections(conn, page_id)
        service_cards  = get_all_service_cards(conn)
        portfolio_items= get_all_portfolio_items(conn)
        initiatives    = get_all_initiatives(conn)

    return render_template('admin/edit_page.html',
        s=s, page=page, sections=sections,
        service_cards=service_cards,
        portfolio_items=portfolio_items,
        initiatives=initiatives,
        themes=THEMES, schemes=COLOR_SCHEMES)


@app.route('/admin/pages/<int:page_id>/delete', methods=['POST'])
@login_required
def admin_delete_page(page_id):
    with db() as conn:
        page = get_page_by_id(conn, page_id)
        if page and page.get('is_home'):
            flash('Cannot delete the home page.', 'error')
            return redirect('/admin/pages')
        p = _p()
        conn.cursor().execute(f"DELETE FROM sections WHERE page_id={p}", (page_id,))
        conn.cursor().execute(f"DELETE FROM pages WHERE id={p}", (page_id,))
    flash('Page deleted.', 'success')
    return redirect('/admin/pages')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — SECTIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/sections/add/<int:page_id>', methods=['POST'])
@login_required
def admin_add_section(page_id):
    f = request.form
    sec_type = f.get('type', 'content')
    p = _p()
    with db() as conn:
        conn.cursor().execute(
            f"INSERT INTO sections (page_id, type, heading, subheading, content, enabled, ord) VALUES ({p},{p},{p},{p},{p},1,100)",
            (page_id, sec_type, f.get('heading',''), f.get('subheading',''), f.get('content',''))
        )
    flash('Section added.', 'success')
    return redirect(f'/admin/pages/{page_id}')


@app.route('/admin/sections/<int:sec_id>', methods=['POST'])
@login_required
def admin_update_section(sec_id):
    f = request.form
    p = _p()

    # Handle image upload for section
    image_url = f.get('image_url_existing', '')
    img_file  = request.files.get('image')
    if img_file and img_file.filename and allowed_image(img_file.filename):
        image_url = save_upload(img_file)

    with db() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT page_id FROM sections WHERE id={p}", (sec_id,))
        row = cur.fetchone()
        page_id = row['page_id'] if hasattr(row, 'keys') else row[0]

        cur.execute(
            f"""UPDATE sections SET
                heading={p}, subheading={p}, content={p},
                button_text={p}, button_link={p}, button_new_tab={p},
                image_url={p}, image_alt={p},
                bg_color={p}, bg_image={p}, text_color={p},
                enabled={p}, ord={p}
            WHERE id={p}""",
            (
                f.get('heading',''), f.get('subheading',''), f.get('content',''),
                f.get('button_text',''), f.get('button_link',''),
                1 if f.get('button_new_tab') else 0,
                image_url, f.get('image_alt',''),
                f.get('bg_color',''), f.get('bg_image',''), f.get('text_color',''),
                1 if f.get('enabled') else 0,
                int(f.get('ord', 0)),
                sec_id
            )
        )
    flash('Section updated.', 'success')
    return redirect(f'/admin/pages/{page_id}')


@app.route('/admin/sections/<int:sec_id>/delete', methods=['POST'])
@login_required
def admin_delete_section(sec_id):
    p = _p()
    with db() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT page_id FROM sections WHERE id={p}", (sec_id,))
        row = cur.fetchone()
        page_id = row['page_id'] if hasattr(row, 'keys') else row[0]
        cur.execute(f"DELETE FROM sections WHERE id={p}", (sec_id,))
    flash('Section deleted.', 'success')
    return redirect(f'/admin/pages/{page_id}')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/nav', methods=['GET', 'POST'])
@login_required
def admin_nav():
    with db() as conn:
        s   = get_settings(conn)
        if request.method == 'POST':
            action = request.form.get('action')
            p = _p()
            if action == 'add':
                conn.cursor().execute(
                    f"INSERT INTO nav (label, url, icon, ord) VALUES ({p},{p},{p},100)",
                    (request.form.get('label',''), request.form.get('url',''), request.form.get('icon',''))
                )
                flash('Nav link added.', 'success')
            elif action == 'delete':
                conn.cursor().execute(
                    f"DELETE FROM nav WHERE id={p}", (request.form.get('id'),)
                )
                flash('Nav link removed.', 'success')
            return redirect('/admin/nav')
        nav = get_nav(conn)
    return render_template('admin/nav.html', s=s, nav=nav)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — INITIATIVES / CTAs
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/initiatives', methods=['GET', 'POST'])
@login_required
def admin_initiatives():
    with db() as conn:
        s = get_settings(conn)
        if request.method == 'POST':
            action = request.form.get('action')
            p = _p()
            if action == 'add':
                f = request.form
                conn.cursor().execute(
                    f"""INSERT INTO initiatives
                        (title, icon, description, button_text, button_link, button_new_tab,
                         icon_style, icon_border, icon_hover, card_hover, card_hover_color,
                         card_hover_font_color, icon_color, card_transition_speed)
                        VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})""",
                    (f.get('title',''), f.get('icon',''), f.get('description',''),
                     f.get('button_text',''), f.get('button_link',''),
                     1 if f.get('button_new_tab') else 0,
                     f.get('icon_style','default'), f.get('icon_border','none'),
                     f.get('icon_hover','zoom'), f.get('card_hover','lift'),
                     f.get('card_hover_color','#000000'), f.get('card_hover_font_color','#ffffff'),
                     f.get('icon_color','#DC143C'), f.get('card_transition_speed','normal'))
                )
                flash('Initiative added.', 'success')
            elif action == 'delete':
                conn.cursor().execute(
                    f"DELETE FROM initiatives WHERE id={p}", (request.form.get('id'),)
                )
                flash('Initiative deleted.', 'success')
            return redirect('/admin/initiatives')
        initiatives = get_all_initiatives(conn)
    return render_template('admin/initiatives.html', s=s, initiatives=initiatives)


@app.route('/admin/initiatives/<int:init_id>', methods=['POST'])
@login_required
def admin_update_initiative(init_id):
    f = request.form
    p = _p()
    with db() as conn:
        conn.cursor().execute(
            f"""UPDATE initiatives SET
                title={p}, icon={p}, description={p},
                button_text={p}, button_link={p}, button_new_tab={p},
                icon_style={p}, icon_border={p}, icon_hover={p},
                card_hover={p}, card_hover_color={p}, card_hover_font_color={p},
                icon_color={p}, card_transition_speed={p}
            WHERE id={p}""",
            (f.get('title',''), f.get('icon',''), f.get('description',''),
             f.get('button_text',''), f.get('button_link',''),
             1 if f.get('button_new_tab') else 0,
             f.get('icon_style','default'), f.get('icon_border','none'),
             f.get('icon_hover','zoom'), f.get('card_hover','lift'),
             f.get('card_hover_color','#000000'), f.get('card_hover_font_color','#ffffff'),
             f.get('icon_color','#DC143C'), f.get('card_transition_speed','normal'),
             init_id)
        )
    flash('Initiative updated.', 'success')
    return redirect('/admin/initiatives')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — SERVICE CARDS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/service-cards', methods=['GET', 'POST'])
@login_required
def admin_service_cards():
    with db() as conn:
        s = get_settings(conn)
        if request.method == 'POST':
            action = request.form.get('action')
            p = _p()
            if action == 'add':
                f = request.form
                conn.cursor().execute(
                    f"INSERT INTO service_cards (title, icon, description, enabled) VALUES ({p},{p},{p},1)",
                    (f.get('title',''), f.get('icon',''), f.get('description',''))
                )
                flash('Service card added.', 'success')
            elif action == 'delete':
                conn.cursor().execute(
                    f"DELETE FROM service_cards WHERE id={p}", (request.form.get('id'),)
                )
                flash('Service card deleted.', 'success')
            return redirect('/admin/service-cards')
        cards = get_all_service_cards(conn)
    return render_template('admin/service_cards.html', s=s, cards=cards)


@app.route('/admin/service-cards/<int:card_id>', methods=['POST'])
@login_required
def admin_update_service_card(card_id):
    f = request.form
    p = _p()
    with db() as conn:
        conn.cursor().execute(
            f"UPDATE service_cards SET title={p}, icon={p}, description={p}, enabled={p} WHERE id={p}",
            (f.get('title',''), f.get('icon',''), f.get('description',''),
             1 if f.get('enabled') else 0, card_id)
        )
    flash('Service card updated.', 'success')
    return redirect('/admin/service-cards')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — PORTFOLIO ITEMS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/portfolio-items', methods=['GET', 'POST'])
@login_required
def admin_portfolio_items():
    with db() as conn:
        s = get_settings(conn)
        if request.method == 'POST':
            action = request.form.get('action')
            p = _p()
            if action == 'add':
                f = request.form
                conn.cursor().execute(
                    f"""INSERT INTO portfolio_items
                        (title, icon, description, link, link_new_tab, enabled)
                        VALUES ({p},{p},{p},{p},{p},1)""",
                    (f.get('title',''), f.get('icon',''), f.get('description',''),
                     f.get('link',''), 1 if f.get('link_new_tab') else 0)
                )
                flash('Portfolio item added.', 'success')
            elif action == 'delete':
                conn.cursor().execute(
                    f"DELETE FROM portfolio_items WHERE id={p}", (request.form.get('id'),)
                )
                flash('Portfolio item deleted.', 'success')
            return redirect('/admin/portfolio-items')
        items = get_all_portfolio_items(conn)
    return render_template('admin/portfolio_items.html', s=s, items=items)


@app.route('/admin/portfolio-items/<int:item_id>', methods=['POST'])
@login_required
def admin_update_portfolio_item(item_id):
    f = request.form
    p = _p()
    with db() as conn:
        conn.cursor().execute(
            f"""UPDATE portfolio_items SET
                title={p}, icon={p}, description={p},
                link={p}, link_new_tab={p}, enabled={p}
            WHERE id={p}""",
            (f.get('title',''), f.get('icon',''), f.get('description',''),
             f.get('link',''), 1 if f.get('link_new_tab') else 0,
             1 if f.get('enabled') else 0, item_id)
        )
    flash('Portfolio item updated.', 'success')
    return redirect('/admin/portfolio-items')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — SOCIAL LINKS
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/socials', methods=['GET', 'POST'])
@login_required
def admin_socials():
    with db() as conn:
        s = get_settings(conn)
        if request.method == 'POST':
            action = request.form.get('action')
            p = _p()
            if action == 'add':
                f = request.form
                conn.cursor().execute(
                    f"INSERT INTO socials (platform, url, icon) VALUES ({p},{p},{p})",
                    (f.get('platform',''), f.get('url',''), f.get('icon',''))
                )
                flash('Social link added.', 'success')
            elif action == 'delete':
                conn.cursor().execute(
                    f"DELETE FROM socials WHERE id={p}", (request.form.get('id'),)
                )
                flash('Social link deleted.', 'success')
            return redirect('/admin/socials')
        socials = get_socials(conn)
    return render_template('admin/socials.html', s=s, socials=socials)

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — GALLERY
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/admin/gallery')
@login_required
def admin_gallery():
    with db() as conn:
        s     = get_settings(conn)
        items = get_all_gallery_items(conn)
        cats  = get_gallery_categories(conn)
    return render_template('admin/gallery.html', s=s, items=items, cats=cats)


@app.route('/admin/gallery/upload', methods=['POST'])
@login_required
def admin_gallery_upload():
    files    = request.files.getlist('media')
    title    = request.form.get('title', '')
    category = request.form.get('category', 'General')
    caption  = request.form.get('caption', '')
    p = _p()
    saved = 0
    with db() as conn:
        for file in files:
            if not file or not file.filename:
                continue
            if not allowed_media(file.filename):
                continue
            fname = save_upload(file)
            ext   = fname.rsplit('.', 1)[-1].lower()
            mtype = 'video' if ext in {'mp4','webm','mov','avi'} else 'image'
            conn.cursor().execute(
                f"INSERT INTO gallery_items (title, caption, media_type, filename, category, enabled) VALUES ({p},{p},{p},{p},{p},1)",
                (title or fname, caption, mtype, fname, category)
            )
            saved += 1
    flash(f'{saved} file(s) uploaded.', 'success')
    return redirect('/admin/gallery')


@app.route('/admin/gallery/<int:item_id>/edit', methods=['POST'])
@login_required
def admin_gallery_edit(item_id):
    f = request.form
    p = _p()
    with db() as conn:
        conn.cursor().execute(
            f"UPDATE gallery_items SET title={p}, category={p}, caption={p} WHERE id={p}",
            (f.get('title',''), f.get('category','General'), f.get('caption',''), item_id)
        )
    flash('Gallery item updated.', 'success')
    return redirect('/admin/gallery')


@app.route('/admin/gallery/<int:item_id>/toggle', methods=['POST'])
@login_required
def admin_gallery_toggle(item_id):
    p = _p()
    with db() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT enabled FROM gallery_items WHERE id={p}", (item_id,))
        row = cur.fetchone()
        if row:
            current = row['enabled'] if hasattr(row, 'keys') else row[0]
            cur.execute(f"UPDATE gallery_items SET enabled={p} WHERE id={p}",
                        (0 if current else 1, item_id))
    return redirect('/admin/gallery')


@app.route('/admin/gallery/<int:item_id>/delete', methods=['POST'])
@login_required
def admin_gallery_delete(item_id):
    p = _p()
    with db() as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT filename FROM gallery_items WHERE id={p}", (item_id,))
        row = cur.fetchone()
        if row:
            fname = row['filename'] if hasattr(row, 'keys') else row[0]
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
        cur.execute(f"DELETE FROM gallery_items WHERE id={p}", (item_id,))
    flash('Gallery item deleted.', 'success')
    return redirect('/admin/gallery')

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN — EXPORT
# ══════════════════════════════════════════════════════════════════════════════

# In-memory export status (good enough for single-worker Render deployment)
_export_status = {}

@app.route('/admin/export')
@login_required
def admin_export():
    with db() as conn:
        s     = get_settings(conn)
        pages = get_pages(conn)
    status = _export_status.copy()
    return render_template('admin/export.html', s=s, pages=pages, status=status)


@app.route('/admin/export/run', methods=['POST'])
@login_required
def admin_export_run():
    global _export_status
    _export_status = {}
    try:
        out_dir  = os.path.join(tempfile.gettempdir(), 'clinton_export_site')
        zip_path = os.path.join(tempfile.gettempdir(), 'clinton_export.zip')

        summary = export_static(app, out_dir)

        if os.path.exists(zip_path):
            os.remove(zip_path)
        zip_export(out_dir, zip_path)

        _export_status = {
            'done':     True,
            'summary':  summary,
            'zip_path': zip_path,
        }
        flash('Export complete! Download your ZIP below.', 'success')
    except Exception as e:
        _export_status = {'error': str(e)}
        flash(f'Export failed: {e}', 'error')

    return redirect('/admin/export')


@app.route('/admin/export/download')
@login_required
def admin_export_download():
    zip_path = _export_status.get('zip_path')
    if not zip_path or not os.path.exists(zip_path):
        flash('No export found. Please run the export first.', 'error')
        return redirect('/admin/export')
    return send_file(
        zip_path,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'clinton-tech-site-{datetime.now().strftime("%Y%m%d-%H%M")}.zip'
    )

# ══════════════════════════════════════════════════════════════════════════════
# FILE SERVING (uploads)
# ══════════════════════════════════════════════════════════════════════════════

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

# ══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
