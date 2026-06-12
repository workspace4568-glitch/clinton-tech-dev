"""
Clinton Tech Dev Suite — Static Export Engine
Renders every page through Flask's test client, rewrites all asset
paths to relative, copies every image/video/font, and zips the result
into a self-contained offline website.
"""
import os, re, shutil, zipfile, mimetypes
from datetime import datetime
from urllib.parse import urlparse, urljoin
from html.parser import HTMLParser

# ── Helpers ──────────────────────────────────────────────────────────────────

def _slug_to_path(slug):
    """Map a URL path to a filesystem path inside the export folder."""
    slug = slug.strip('/')
    if not slug or slug == 'home':
        return 'index.html'
    if slug == 'gallery':
        return 'gallery/index.html'
    return f"{slug}/index.html"

def _rewrite_html(html: str, depth: int) -> str:
    """
    Rewrite all absolute internal paths to relative ones so the site
    works when opened from any folder on disk.
    depth = number of directories deep this file lives (0 = root).
    """
    prefix = '../' * depth if depth > 0 else './'

    def fix(m):
        attr, quote, url = m.group(1), m.group(2), m.group(3)
        url = url.strip()
        # Skip external links, anchors, mailto/tel, data URIs
        if (url.startswith('http') or url.startswith('mailto:')
                or url.startswith('tel:') or url.startswith('data:')
                or url.startswith('#') or url.startswith('javascript:')):
            return m.group(0)

        # Strip leading slash
        clean = url.lstrip('/')

        # Internal pages  →  page/index.html
        if clean == '' or clean == 'home':
            rel = f'{prefix}index.html'
        elif clean.startswith('page/'):
            page_slug = clean[5:].rstrip('/')
            rel = f'{prefix}{page_slug}/index.html'
        elif clean == 'gallery':
            rel = f'{prefix}gallery/index.html'
        elif clean.startswith('uploads/'):
            rel = f'{prefix}{clean}'
        elif clean.startswith('static/'):
            rel = f'{prefix}{clean}'
        else:
            rel = f'{prefix}{clean}'

        return f'{attr}={quote}{rel}{quote}'

    # Rewrite href="..." src="..." action="..."
    html = re.sub(
        r'(href|src|action)=(["\'])([^"\']*)\2',
        fix,
        html
    )

    # Rewrite inline style background-image: url('/uploads/...')
    def fix_inline_bg(m):
        full_style = m.group(0)
        def fix_url_in_style(um):
            raw = um.group(1).strip("'\"")
            if (raw.startswith('http') or raw.startswith('data:') or raw.startswith('#')):
                return um.group(0)
            clean = raw.lstrip('/')
            return f"url('{prefix}{clean}')"
        return re.sub(r"url\(([^)]+)\)", fix_url_in_style, full_style)

    html = re.sub(r'style="[^"]*url\([^)]+\)[^"]*"', fix_inline_bg, html)

    # Rewrite CSS url(...) references inside <style> blocks
    def fix_style_block_url(m):
        url = m.group(1).strip('\'"')
        if (url.startswith('http') or url.startswith('data:') or url.startswith('#')):
            return m.group(0)
        clean = url.lstrip('/')
        return f"url('{prefix}{clean}')"

    # Only fix non-http url() references inside style tags
    def fix_style_block(m):
        block = m.group(0)
        block = re.sub(r"url\((['\"]?)(?!http|data:)([^)'\"]+)(['\"]?)\)",
                       lambda x: f"url('{prefix}{x.group(2).lstrip('/')}')",
                       block)
        return block

    html = re.sub(r'<style[^>]*>.*?</style>', fix_style_block, html, flags=re.DOTALL)

    # Remove admin-only links entirely (they don't exist in static export)
    html = re.sub(r'href=["\']/?admin[^"\']*["\']', 'href="#"', html)

    # For push-style nav: the page-wrapper transform needs no JS in static export
    html = html.replace('class="page-wrapper"', 'class="page-wrapper" style="transform:none!important"')

    return html



    return html


class _AssetFinder(HTMLParser):
    """Parse HTML and collect all local asset URLs (src, href for css/fonts)."""
    def __init__(self):
        super().__init__()
        self.assets = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for attr in ('src', 'href', 'data-src'):
            url = attrs.get(attr, '')
            if url and not url.startswith(('http', 'data:', '#', 'mailto:', 'tel:', 'javascript:')):
                self.assets.add(url.lstrip('/'))
        # Inline style background
        style = attrs.get('style', '')
        for m in re.finditer(r"url\(['\"]?([^)'\"]+)['\"]?\)", style):
            u = m.group(1)
            if not u.startswith(('http', 'data:')):
                self.assets.add(u.lstrip('/'))


# ── Main export function ──────────────────────────────────────────────────────

def export_static(app, out_dir: str) -> dict:
    """
    Export the entire site to `out_dir` as static HTML.
    Returns a summary dict with counts and any errors.
    """
    summary = {'pages': 0, 'assets': 0, 'errors': []}

    # Wipe and recreate output directory
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir)

    project_root = os.path.dirname(os.path.abspath(app.root_path))
    if not project_root or project_root == '/':
        project_root = os.path.dirname(os.path.abspath(__file__))

    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')

    # ── Collect all pages to render ─────────────────────────────────────────
    from database import db, get_pages, get_gallery_items, get_gallery_categories, init_gallery

    with db() as conn:
        pages = get_pages(conn)
        init_gallery(conn)
        gallery_items = get_gallery_items(conn, enabled_only=True)
        gallery_cats  = ['All'] + get_gallery_categories(conn)

    routes_to_render = ['/']                                          # home
    for page in pages:
        if not page['is_home'] and page['visible']:
            routes_to_render.append(f"/page/{page['slug']}")
    routes_to_render.append('/gallery')                               # gallery (always)
    for cat in gallery_cats:
        if cat != 'All':
            routes_to_render.append(f"/gallery?cat={cat}")

    # ── Render each page ────────────────────────────────────────────────────
    all_assets = set()

    with app.test_client() as client:
        for route in routes_to_render:
            try:
                resp = client.get(route)
                if resp.status_code != 200:
                    summary['errors'].append(f"HTTP {resp.status_code} on {route}")
                    continue

                html = resp.data.decode('utf-8', errors='replace')

                # Collect assets from this page
                parser = _AssetFinder()
                parser.feed(html)
                all_assets.update(parser.assets)

                # Determine output path and depth
                path_part = route.split('?')[0]
                if path_part == '/':
                    rel_path = 'index.html'
                    depth = 0
                elif path_part == '/gallery':
                    # gallery category pages all go in gallery/
                    q = route.split('?cat=')
                    if len(q) > 1 and q[1] != 'All':
                        cat_slug = q[1].lower().replace(' ', '-')
                        rel_path = f"gallery/{cat_slug}/index.html"
                        depth = 2
                    else:
                        rel_path = 'gallery/index.html'
                        depth = 1
                else:
                    slug = path_part.lstrip('/page/')
                    rel_path = f"{slug}/index.html"
                    depth = 1

                # Rewrite HTML
                html = _rewrite_html(html, depth)

                # Write file
                dest = os.path.join(out_dir, rel_path)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(html)

                summary['pages'] += 1

            except Exception as e:
                summary['errors'].append(f"Error on {route}: {e}")

    # ── Copy all local assets ────────────────────────────────────────────────
    # Add known static assets
    all_assets.update([
        'static/uploads',  # will be handled separately
    ])

    # Copy uploads directory
    if os.path.isdir(uploads_dir):
        dest_uploads = os.path.join(out_dir, 'uploads')
        shutil.copytree(uploads_dir, dest_uploads, dirs_exist_ok=True)
        for f in os.listdir(dest_uploads):
            summary['assets'] += 1

    # Copy anything in static/ except uploads
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    if os.path.isdir(static_dir):
        dest_static = os.path.join(out_dir, 'static')
        for item in os.listdir(static_dir):
            if item == 'uploads':
                continue
            src = os.path.join(static_dir, item)
            dst = os.path.join(dest_static, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                os.makedirs(dest_static, exist_ok=True)
                shutil.copy2(src, dst)

    # ── Write a helpful offline README ──────────────────────────────────────
    _write_offline_readme(out_dir, summary)

    return summary


def _write_offline_readme(out_dir, summary):
    readme = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Offline Site — How to Open</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:640px;margin:60px auto;padding:0 24px;color:#1a1a1a;line-height:1.7;}}
  h1{{font-size:1.8rem;margin-bottom:8px;}}
  code{{background:#f0f0f0;padding:2px 8px;border-radius:4px;font-size:.9rem;}}
  .tip{{background:#f0f7ff;border-left:4px solid #0077B6;padding:16px 20px;border-radius:0 8px 8px 0;margin:20px 0;}}
  .stat{{display:inline-block;background:#0077B618;color:#0077B6;padding:4px 12px;border-radius:4px;font-weight:700;margin-right:8px;}}
</style>
</head>
<body>
<h1>Clinton Tech Dev Suite — Offline Export</h1>
<p>Generated: <strong>{datetime.now().strftime('%B %d, %Y at %H:%M')}</strong></p>
<p>
  <span class="stat">{summary['pages']} pages</span>
  <span class="stat">{summary['assets']} media files</span>
</p>

<h2>How to open</h2>
<p>Double-click <code>index.html</code> in this folder to open the site in your browser. All pages, images, and videos are included — no internet connection needed.</p>

<div class="tip">
  <strong>Tip:</strong> For the best experience (especially with videos and fonts), open via a local server:<br><br>
  <code>cd path/to/this/folder</code><br>
  <code>python -m http.server 8080</code><br><br>
  Then visit <code>http://localhost:8080</code>
</div>

<h2>Folder structure</h2>
<pre style="background:#f5f5f5;padding:16px;border-radius:8px;font-size:.85rem;">
index.html          ← Homepage
gallery/
  index.html        ← Gallery page
[page-slug]/
  index.html        ← Each custom page
uploads/            ← All images and videos
static/             ← CSS, JS (if any)
HOW_TO_OPEN.html    ← This file
</pre>

{'<h2>Errors during export</h2><ul>' + ''.join(f'<li>{e}</li>' for e in summary['errors']) + '</ul>' if summary['errors'] else ''}
</body>
</html>"""
    with open(os.path.join(out_dir, 'HOW_TO_OPEN.html'), 'w') as f:
        f.write(readme)


# ── ZIP helper ───────────────────────────────────────────────────────────────

def zip_export(out_dir: str, zip_path: str) -> int:
    """Zip the export folder. Returns total file count."""
    count = 0
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for root, dirs, files in os.walk(out_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                arc_name = os.path.relpath(abs_path, os.path.dirname(out_dir))
                zf.write(abs_path, arc_name)
                count += 1
    return count
