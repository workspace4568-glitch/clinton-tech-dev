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
        font_mono TEXT DEFAULT ''
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
        button_text TEXT DEFAULT '',
        button_link TEXT DEFAULT '',
        button_new_tab INTEGER DEFAULT 0
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
        font_heading TEXT DEFAULT '', font_body TEXT DEFAULT '', font_mono TEXT DEFAULT '')""",
    """CREATE TABLE IF NOT EXISTS pages (
        id SERIAL PRIMARY KEY, title TEXT, slug TEXT UNIQUE,
        is_home INTEGER DEFAULT 0, visible INTEGER DEFAULT 1, ord INTEGER DEFAULT 0)""",
    """CREATE TABLE IF NOT EXISTS sections (
        id SERIAL PRIMARY KEY, page_id INTEGER REFERENCES pages(id),
        type TEXT DEFAULT 'content', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1,
        heading TEXT DEFAULT '', subheading TEXT DEFAULT '', content TEXT DEFAULT '',
        image_url TEXT DEFAULT '', image_alt TEXT DEFAULT '',
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
        icon TEXT DEFAULT 'fa-solid fa-star', ord INTEGER DEFAULT 0, enabled INTEGER DEFAULT 1)""",
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
    ]
    for table, col, col_def in migrations:
        try:
            if USE_POSTGRES:
                conn.cursor().execute(
                    f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"
                )
            else:
                conn.execute(
                    f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"
                )
        except Exception:
            pass  # Column already exists — safe to ignore

# ── Query Helpers ─────────────────────────────────────────────────────────────
def _row(r):
    if r is None: return None
    return dict(r)

def _rows(rs):
    return [dict(r) for r in rs]

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
    return _rows(cur.fetchall())

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

def count(conn, table):
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    r = cur.fetchone()
    return r[0] if r else 0

def last_insert_id(conn, table='pages'):
    """Get last inserted ID — handles SQLite and PostgreSQL."""
    cur = conn.cursor()
    if USE_POSTGRES:
        cur.execute(f"SELECT lastval()")
    else:
        cur.execute("SELECT last_insert_rowid()")
    return cur.fetchone()[0]

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
    return [r[0] for r in cur.fetchall()]

def get_all_gallery_items(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM gallery_items ORDER BY ord, id")
    return _rows(cur.fetchall())
