"""
Clinton Tech Dev Suite — Database Layer
Supports SQLite (local dev) and PostgreSQL (Render production).
No ORM required — uses Python's built-in sqlite3 and psycopg2.
"""
import os, sqlite3
from contextlib import contextmanager

# ── Connection Setup ──────────────────────────────────────────────────────────
# Render provides DATABASE_URL as postgres:// — psycopg2 needs postgresql://
_RAW_URL = os.environ.get('DATABASE_URL', '')
DATABASE_URL = _RAW_URL.replace('postgres://', 'postgresql://', 1) if _RAW_URL.startswith('postgres://') else _RAW_URL

USE_POSTGRES = bool(DATABASE_URL and 'postgresql' in DATABASE_URL)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'clinton.db')

@contextmanager
def db():
    if USE_POSTGRES:
        import psycopg2, psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        conn.autocommit = False
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

def _p():
    """Return the correct SQL placeholder for the active database."""
    return '%s' if USE_POSTGRES else '?'

# ── Schema ────────────────────────────────────────────────────────────────────
_SQLITE_SCHEMA = """
    CREATE TABLE IF NOT EXISTS site_settings (
        id INTEGER PRIMARY KEY,
        site_name TEXT DEFAULT 'Clinton Tech Dev Suite',
        tagline TEXT DEFAULT 'Professional Web Development',
        theme TEXT DEFAULT 'bold-studio',
        color_scheme TEXT DEFAULT 'crimson-black',
        logo_url TEXT DEFAULT '',
        favicon_url TEXT DEFAULT '',
        footer_text TEXT DEFAULT '© 2024 Clinton Tech Dev Suite. All rights reserved.',
        contact_email TEXT DEFAULT '',
        contact_phone TEXT DEFAULT '',
        contact_address TEXT DEFAULT '',
        contact_hours TEXT DEFAULT '',
        meta_title TEXT DEFAULT 'Clinton Tech Dev Suite',
        meta_description TEXT DEFAULT '',
        animations_enabled INTEGER DEFAULT 1,
        announcement_bar_enabled INTEGER DEFAULT 0,
        announcement_text TEXT DEFAULT '',
        announcement_link TEXT DEFAULT '',
        maintenance_mode INTEGER DEFAULT 0,
        maintenance_message TEXT DEFAULT 'Under maintenance. Back soon!',
        button_style TEXT DEFAULT 'solid',
        button_radius INTEGER DEFAULT 6,
        container_max_width INTEGER DEFAULT 1200,
        container_justify TEXT DEFAULT 'center',
        nav_style TEXT DEFAULT 'slide-right',
        font_heading TEXT DEFAULT '',
        font_body TEXT DEFAULT '',
        font_mono TEXT DEFAULT '',
        hero_position TEXT DEFAULT 'relative',
        hero_height TEXT DEFAULT 'screen',
        logo_border_radius TEXT DEFAULT '50',
        logo_border_width INTEGER DEFAULT 0,
        logo_border_color TEXT DEFAULT '',
        logo_bg_color TEXT DEFAULT '',
        logo_show_name INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        slug TEXT UNIQUE,
        is_home INTEGER DEFAULT 0,
        visible INTEGER DEFAULT 1,
        ord INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_id INTEGER REFERENCES pages(id),
        type TEXT DEFAULT 'content',
        ord INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        heading TEXT DEFAULT '',
        subheading TEXT DEFAULT '',
        content TEXT DEFAULT '',
        image_url TEXT DEFAULT '',
        image_alt TEXT DEFAULT '',
        image_position TEXT DEFAULT 'center',
        image_size TEXT DEFAULT 'cover',
        image_overlay REAL DEFAULT 0.0,
        image_overlay_color TEXT DEFAULT '#000000',
        image_blur INTEGER DEFAULT 0,
        section_bg_color TEXT DEFAULT '',
        bg_attachment TEXT DEFAULT 'scroll',
        icon_style TEXT DEFAULT 'default',
        icon_border TEXT DEFAULT 'none',
        icon_hover TEXT DEFAULT 'zoom',
        icon_color TEXT DEFAULT '',
        card_hover TEXT DEFAULT 'lift',
        card_hover_color TEXT DEFAULT '',
        card_hover_font_color TEXT DEFAULT '',
        card_transition_speed TEXT DEFAULT 'normal',
        button_text TEXT DEFAULT '',
        button_link TEXT DEFAULT '',
        button_new_tab INTEGER DEFAULT 0,
        heading_color TEXT DEFAULT '',
        heading_align TEXT DEFAULT 'left',
        subheading_color TEXT DEFAULT '',
        card_bg_color TEXT DEFAULT '',
        card_border_width INTEGER DEFAULT 0,
        card_border_color TEXT DEFAULT '',
        card_border_radius INTEGER DEFAULT 8,
        image_urls TEXT DEFAULT '',
        image_collage TEXT DEFAULT 'single',
        gallery_preset TEXT DEFAULT 'masonry'
    );
    CREATE TABLE IF NOT EXISTS nav_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        label TEXT,
        url TEXT,
        icon TEXT DEFAULT '',
        ord INTEGER DEFAULT 0,
        open_new_tab INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS social_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT,
        url TEXT,
        icon TEXT DEFAULT 'fa-solid fa-link'
    );
    CREATE TABLE IF NOT EXISTS initiatives (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        description TEXT DEFAULT '',
        button_text TEXT DEFAULT 'Learn More',
        button_link TEXT DEFAULT '#',
        button_new_tab INTEGER DEFAULT 0,
        icon TEXT DEFAULT 'fa-solid fa-star',
        ord INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        icon_style TEXT DEFAULT 'default',
        icon_border TEXT DEFAULT 'none',
        icon_hover TEXT DEFAULT 'zoom',
        icon_color TEXT DEFAULT '',
        card_hover TEXT DEFAULT 'lift',
        card_hover_color TEXT DEFAULT '',
        card_hover_font_color TEXT DEFAULT '',
        card_transition_speed TEXT DEFAULT 'normal'
    );
    CREATE TABLE IF NOT EXISTS service_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT '',
        description TEXT DEFAULT '',
        icon TEXT DEFAULT 'fa-solid fa-star',
        ord INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS portfolio_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT '',
        description TEXT DEFAULT '',
        icon TEXT DEFAULT 'fa-solid fa-briefcase',
        link TEXT DEFAULT '',
        link_new_tab INTEGER DEFAULT 0,
        ord INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1
    );
"""

_PG_TABLES = [
    """CREATE TABLE IF NOT EXISTS site_settings (
        id SERIAL PRIMARY KEY, site_name TEXT DEFAULT 'Clinton Tech Dev Suite',
        tagline TEXT DEFAULT 'Professional Web Development', theme TEXT DEFAULT 'bold-studio',
        color_scheme TEXT DEFAULT 'crimson-black', logo_url TEXT DEFAULT '',
        favicon_url TEXT DEFAULT '', footer_text TEXT DEFAULT '© 2024 Clinton Tech Dev Suite. All rights reserved.',
        contact_email TEXT DEFAULT '', contact_phone TEXT DEFAULT '',
        contact_address TEXT DEFAULT '', contact_hours TEXT DEFAULT '',
        meta_title TEXT DEFAULT 'Clinton Tech Dev Suite', meta_description TEXT DEFAULT '',
        animations_enabled INTEGER DEFAULT 1, announcement_bar_enabled INTEGER DEFAULT 0,
        announcement_text TEXT DEFAULT '', announcement_link TEXT DEFAULT '',
        maintenance_mode INTEGER DEFAULT 0, maintenance_message TEXT DEFAULT 'Under maintenance. Back soon!',
        button_style TEXT DEFAULT 'solid', button_radius INTEGER DEFAULT 6,
        container_max_width INTEGER DEFAULT 1200, container_justify TEXT DEFAULT 'center',
        nav_style TEXT DEFAULT 'slide-right',
        hero_position TEXT DEFAULT 'relative', hero_height TEXT DEFAULT 'screen',
        logo_border_radius TEXT DEFAULT '50', logo_border_width INTEGER DEFAULT 0,
        logo_border_color TEXT DEFAULT '', logo_bg_color TEXT DEFAULT '',
        logo_show_name INTEGER DEFAULT 0,
        font_heading TEXT DEFAULT '', font_body TEXT DEFAULT '', font_mono TEXT DEFAULT '')""",
    """CREATE TABLE IF NOT EXISTS pages (
        id SERIAL PRIMARY KEY, title TEXT, slug TEXT UNIQUE,
        is_home INTEGER DEFAULT 0, visible INTEGER DEFAULT 1, ord INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS sections (
        id SERIAL PRIMARY KEY, page_id INTEGER REFERENCES pages(id),
        type TEXT DEFAULT 'content', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1,
        heading TEXT DEFAULT '', subheading TEXT DEFAULT '', content TEXT DEFAULT '',
        image_url TEXT DEFAULT '', image_alt TEXT DEFAULT '',
        image_position TEXT DEFAULT 'center', image_size TEXT DEFAULT 'cover',
        image_overlay REAL DEFAULT 0.0, image_overlay_color TEXT DEFAULT '#000000',
        image_blur INTEGER DEFAULT 0,
        section_bg_color TEXT DEFAULT '', bg_attachment TEXT DEFAULT 'scroll',
        icon_style TEXT DEFAULT 'default', icon_border TEXT DEFAULT 'none', icon_hover TEXT DEFAULT 'zoom',
        button_text TEXT DEFAULT '', button_link TEXT DEFAULT '',
        button_new_tab INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS nav_items (
        id SERIAL PRIMARY KEY, label TEXT, url TEXT,
        icon TEXT DEFAULT '', ord INTEGER DEFAULT 0, open_new_tab INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS social_links (
        id SERIAL PRIMARY KEY, platform TEXT, url TEXT, icon TEXT DEFAULT 'fa-solid fa-link')""",
    """CREATE TABLE IF NOT EXISTS initiatives (
        id SERIAL PRIMARY KEY, title TEXT, description TEXT DEFAULT '',
        button_text TEXT DEFAULT 'Learn More', button_link TEXT DEFAULT '#',
        button_new_tab INTEGER DEFAULT 0,
        icon TEXT DEFAULT 'fa-solid fa-star', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1,
        icon_style TEXT DEFAULT 'default', icon_border TEXT DEFAULT 'none', icon_hover TEXT DEFAULT 'zoom')""",
    """CREATE TABLE IF NOT EXISTS service_cards (
        id SERIAL PRIMARY KEY, title TEXT DEFAULT '', description TEXT DEFAULT '',
        icon TEXT DEFAULT 'fa-solid fa-star', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""",
    """CREATE TABLE IF NOT EXISTS portfolio_items (
        id SERIAL PRIMARY KEY, title TEXT DEFAULT '', description TEXT DEFAULT '',
        icon TEXT DEFAULT 'fa-solid fa-briefcase', link TEXT DEFAULT '',
        link_new_tab INTEGER DEFAULT 0, ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""",
]

def init_db():
    with db() as conn:
        if USE_POSTGRES:
            cur = conn.cursor()
            for sql in _PG_TABLES:
                cur.execute(sql)
        else:
            conn.executescript(_SQLITE_SCHEMA)
        _migrate(conn)
        # Ensure newer tables exist even on old databases
        try:
            init_service_cards(conn)
        except Exception:
            pass
        try:
            init_portfolio_items(conn)
        except Exception:
            pass

def _migrate(conn):
    """Safely add new columns to existing databases without breaking anything."""
    migrations = [
        ("sections",      "button_new_tab",       "INTEGER DEFAULT 0"),
        ("initiatives",   "button_new_tab",       "INTEGER DEFAULT 0"),
        ("initiatives",   "button_icon",          "TEXT DEFAULT ''"),
        ("site_settings", "container_max_width",  "INTEGER DEFAULT 1200"),
        ("site_settings", "container_justify",    "TEXT DEFAULT 'center'"),
        ("site_settings", "nav_style",            "TEXT DEFAULT 'slide-right'"),
        ("site_settings", "font_heading",         "TEXT DEFAULT ''"),
        ("site_settings", "font_body",            "TEXT DEFAULT ''"),
        ("site_settings", "font_mono",            "TEXT DEFAULT ''"),
        ("sections", "image_position",      "TEXT DEFAULT 'center'"),
        ("sections", "image_size",          "TEXT DEFAULT 'cover'"),
        ("sections", "image_overlay",       "REAL DEFAULT 0.0"),
        ("sections", "image_overlay_color", "TEXT DEFAULT '#000000'"),
        ("sections", "image_blur",          "INTEGER DEFAULT 0"),
        ("sections", "icon_style",          "TEXT DEFAULT 'default'"),
        ("sections", "icon_border",         "TEXT DEFAULT 'none'"),
        ("sections", "icon_hover",          "TEXT DEFAULT 'zoom'"),
        ("initiatives", "icon_style",       "TEXT DEFAULT 'default'"),
        ("initiatives", "icon_border",      "TEXT DEFAULT 'none'"),
        ("initiatives", "icon_hover",       "TEXT DEFAULT 'zoom'"),
        # site_settings columns added in later versions
        ("site_settings", "button_style",        "TEXT DEFAULT 'solid'"),
        ("site_settings", "button_radius",       "INTEGER DEFAULT 6"),
        ("site_settings", "contact_hours",       "TEXT DEFAULT ''"),
        ("site_settings", "hero_position",       "TEXT DEFAULT 'relative'"),
        ("site_settings", "hero_height",         "TEXT DEFAULT 'screen'"),
        ("site_settings", "nav_style",           "TEXT DEFAULT 'slide-right'"),
        ("site_settings", "font_heading",        "TEXT DEFAULT ''"),
        ("site_settings", "font_body",           "TEXT DEFAULT ''"),
        ("site_settings", "font_mono",           "TEXT DEFAULT ''"),
        ("site_settings", "container_max_width", "INTEGER DEFAULT 1200"),
        ("site_settings", "container_justify",   "TEXT DEFAULT 'center'"),
        # logo styling
        ("site_settings", "logo_border_radius",  "TEXT DEFAULT '50'"),
        ("site_settings", "logo_border_width",   "INTEGER DEFAULT 0"),
        ("site_settings", "logo_border_color",   "TEXT DEFAULT ''"),
        ("site_settings", "logo_bg_color",       "TEXT DEFAULT ''"),
        ("site_settings", "logo_show_name",      "INTEGER DEFAULT 0"),
        # sections columns missing from UPDATE query
        ("sections", "section_bg_color",         "TEXT DEFAULT ''"),
        ("sections", "bg_attachment",            "TEXT DEFAULT 'scroll'"),
        ("sections", "icon_color",               "TEXT DEFAULT ''"),
        ("sections", "card_hover",               "TEXT DEFAULT 'lift'"),
        ("sections", "card_hover_color",         "TEXT DEFAULT ''"),
        ("sections", "card_hover_font_color",    "TEXT DEFAULT ''"),
        ("sections", "card_transition_speed",    "TEXT DEFAULT 'normal'"),
        ("sections", "heading_color",              "TEXT DEFAULT ''"),
        ("sections", "heading_align",              "TEXT DEFAULT 'left'"),
        ("sections", "subheading_color",           "TEXT DEFAULT ''"),
        ("sections", "card_bg_color",              "TEXT DEFAULT ''"),
        ("sections", "card_border_width",          "INTEGER DEFAULT 0"),
        ("sections", "card_border_color",          "TEXT DEFAULT ''"),
        ("sections", "card_border_radius",         "INTEGER DEFAULT 8"),
        ("sections", "image_urls",                 "TEXT DEFAULT ''"),
        ("sections", "image_collage",              "TEXT DEFAULT 'single'"),
        ("sections", "gallery_preset",             "TEXT DEFAULT 'masonry'"),
    ]
    for table, col, col_def in migrations:
        if USE_POSTGRES:
            cur = conn.cursor()
            try:
                cur.execute("SAVEPOINT _migrate_sp")
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
                cur.execute("RELEASE SAVEPOINT _migrate_sp")
            except Exception:
                cur.execute("ROLLBACK TO SAVEPOINT _migrate_sp")  # keeps transaction alive
        else:
            try:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}")
            except Exception:
                pass  # Column already exists — safe to ignore

# ── Query Helpers ─────────────────────────────────────────────────────────────
def _row(r):
    if r is None: return None
    return dict(r)

def _rows(rs):
    return [dict(r) for r in rs]

# Default values for section fields — ensures templates never crash on missing columns
_SECTION_DEFAULTS = {
    'image_url': '', 'image_alt': '',
    'image_position': 'center', 'image_size': 'cover',
    'image_overlay': 0.0, 'image_overlay_color': '#000000', 'image_blur': 0,
    'section_bg_color': '', 'bg_attachment': 'scroll',
    'icon_style': 'default', 'icon_border': 'none', 'icon_hover': 'zoom',
    'button_text': '', 'button_link': '', 'button_new_tab': 0,
    'heading': '', 'subheading': '', 'content': '', 'enabled': 1,
    'heading_color': '', 'heading_align': 'left',
    'subheading_color': '', 'card_bg_color': '',
    'card_border_width': 0, 'card_border_color': '', 'card_border_radius': 8,
    'image_urls': '', 'image_collage': 'single', 'gallery_preset': 'masonry',
}

def _section(d):
    """Fill in any missing section keys with safe defaults."""
    out = dict(_SECTION_DEFAULTS)
    out.update({k: v for k, v in d.items() if v is not None})
    # Ensure numeric fields are correct types
    try: out['image_overlay'] = float(out['image_overlay'] or 0)
    except: out['image_overlay'] = 0.0
    try: out['image_blur'] = int(out['image_blur'] or 0)
    except: out['image_blur'] = 0
    return out

def get_settings(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM site_settings WHERE id=1")
    row = _row(cur.fetchone())
    if not row:
        cur.execute("INSERT INTO site_settings (id) VALUES (1)")
        conn.commit()
        cur.execute("SELECT * FROM site_settings WHERE id=1")
        row = _row(cur.fetchone())
    return row

def get_pages(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM pages ORDER BY ord")
    return _rows(cur.fetchall())

def get_page_by_slug(conn, slug):
    cur = conn.cursor()
    p = _p()
    cur.execute(f"SELECT * FROM pages WHERE slug={p}", (slug,))
    return _row(cur.fetchone())

def get_page_by_id(conn, page_id):
    cur = conn.cursor()
    p = _p()
    cur.execute(f"SELECT * FROM pages WHERE id={p}", (page_id,))
    return _row(cur.fetchone())

def get_home_page(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM pages WHERE is_home=1")
    return _row(cur.fetchone())

def get_sections(conn, page_id, enabled_only=False):
    cur = conn.cursor()
    p = _p()
    q = f"SELECT * FROM sections WHERE page_id={p}"
    if enabled_only: q += " AND enabled=1"
    q += " ORDER BY ord"
    cur.execute(q, (page_id,))
    return [_section(dict(r)) for r in cur.fetchall()]

def get_nav(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM nav_items ORDER BY ord")
    return _rows(cur.fetchall())

def get_socials(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM social_links")
    return _rows(cur.fetchall())

def get_initiatives(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM initiatives WHERE enabled=1 ORDER BY ord")
    return _rows(cur.fetchall())

def get_all_initiatives(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM initiatives ORDER BY ord")
    return _rows(cur.fetchall())

# ── Service Cards ─────────────────────────────────────────────────────────────
def init_service_cards(conn):
    """Create service_cards table if missing (migration-safe)."""
    if USE_POSTGRES:
        conn.cursor().execute("""CREATE TABLE IF NOT EXISTS service_cards (
            id SERIAL PRIMARY KEY, title TEXT DEFAULT '', description TEXT DEFAULT '',
            icon TEXT DEFAULT 'fa-solid fa-star', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""")
    else:
        conn.execute("""CREATE TABLE IF NOT EXISTS service_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT DEFAULT '', description TEXT DEFAULT '',
            icon TEXT DEFAULT 'fa-solid fa-star', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""")

def get_service_cards(conn, enabled_only=True):
    cur = conn.cursor()
    q = "SELECT * FROM service_cards"
    if enabled_only:
        q += " WHERE enabled=1"
    q += " ORDER BY ord, id"
    cur.execute(q)
    return _rows(cur.fetchall())

def get_all_service_cards(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM service_cards ORDER BY ord, id")
    return _rows(cur.fetchall())

# ── Portfolio Items ───────────────────────────────────────────────────────────
def init_portfolio_items(conn):
    """Create portfolio_items table if missing (migration-safe)."""
    if USE_POSTGRES:
        conn.cursor().execute("""CREATE TABLE IF NOT EXISTS portfolio_items (
            id SERIAL PRIMARY KEY, title TEXT DEFAULT '', description TEXT DEFAULT '',
            icon TEXT DEFAULT 'fa-solid fa-briefcase', link TEXT DEFAULT '',
            link_new_tab INTEGER DEFAULT 0, ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""")
    else:
        conn.execute("""CREATE TABLE IF NOT EXISTS portfolio_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT DEFAULT '', description TEXT DEFAULT '',
            icon TEXT DEFAULT 'fa-solid fa-briefcase', link TEXT DEFAULT '',
            link_new_tab INTEGER DEFAULT 0, ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""")

def get_portfolio_items(conn, enabled_only=True):
    cur = conn.cursor()
    q = "SELECT * FROM portfolio_items"
    if enabled_only:
        q += " WHERE enabled=1"
    q += " ORDER BY ord, id"
    cur.execute(q)
    return _rows(cur.fetchall())

def get_all_portfolio_items(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM portfolio_items ORDER BY ord, id")
    return _rows(cur.fetchall())


def count(conn, table):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
    r = cur.fetchone()
    if r is None:
        return 0
    # RealDictCursor (Postgres) returns a dict; sqlite3.Row supports index access
    try:
        return r['n']
    except (KeyError, TypeError):
        return r[0]

def last_insert_id(conn, table='pages'):
    """Get last inserted ID — handles SQLite and PostgreSQL."""
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute("SELECT lastval() AS id")
    else:
        cur.execute("SELECT last_insert_rowid() AS id")
    r = cur.fetchone()
    try:
        return r['id']
    except (KeyError, TypeError):
        return r[0]

# ── Gallery ───────────────────────────────────────────────────────────────────
_GALLERY_SQLITE = """
    CREATE TABLE IF NOT EXISTS gallery_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT DEFAULT '',
        caption TEXT DEFAULT '',
        media_type TEXT DEFAULT 'image',
        filename TEXT DEFAULT '',
        category TEXT DEFAULT 'General',
        ord INTEGER DEFAULT 0,
        enabled INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );
"""
_GALLERY_PG = """CREATE TABLE IF NOT EXISTS gallery_items (
    id SERIAL PRIMARY KEY, title TEXT DEFAULT '', caption TEXT DEFAULT '',
    media_type TEXT DEFAULT 'image', filename TEXT DEFAULT '',
    category TEXT DEFAULT 'General', ord INTEGER DEFAULT 0,
    enabled INTEGER DEFAULT 1, created_at TIMESTAMP DEFAULT NOW())"""

def init_gallery(conn):
    if USE_POSTGRES:
        conn.cursor().execute(_GALLERY_PG)
    else:
        conn.executescript(_GALLERY_SQLITE)

def get_gallery_items(conn, category=None, enabled_only=True):
    cur = conn.cursor()
    p = _p()
    if category and category != 'All':
        q = f"SELECT * FROM gallery_items WHERE category={p}"
        params = (category,)
        if enabled_only:
            q += f" AND enabled=1"
    else:
        q = "SELECT * FROM gallery_items"
        params = ()
        if enabled_only:
            q += " WHERE enabled=1"
    q += " ORDER BY ord, id"
    cur.execute(q, params)
    return _rows(cur.fetchall())

def get_gallery_categories(conn):
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT category FROM gallery_items WHERE enabled=1 ORDER BY category")
    rows = cur.fetchall()
    return [r['category'] if hasattr(r, 'keys') else r[0] for r in rows]

def get_all_gallery_items(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM gallery_items ORDER BY ord, id")
    return _rows(cur.fetchall())
