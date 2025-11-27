from markdown import markdown
import base64
import zlib
import re
from textwrap import dedent
from django.conf import settings
import bleach

# Import the caching function
from diagramm_proxy.diagram_cache import get_cached_diagram

DIAGRAMMSERVER="/diagramm"

# Allowed HTML tags for bleach sanitization
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'hr',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'img', 'a', 'sup', 'sub', 'span', 'div'
]

ALLOWED_ATTRIBUTES = {
    'img': ['src', 'alt', 'width', 'height'],
    'a': ['href', 'title'],
    'span': ['class'],
    'div': ['class'],
    'p': ['class'],
    'table': ['class'],
    'th': ['colspan', 'rowspan', 'class'],
    'td': ['colspan', 'rowspan', 'class'],
    'pre': ['class'],
    'code': ['class'],
}

def render_textabschnitte(queryset):
    """
    Converts a queryset of Textabschnitt-like models into a list of (typ, html) tuples.
    Applies special formatting for 'liste' and 'tabelle' types.
    """
    output = []

    for abschnitt in queryset:
        typ = abschnitt.abschnitttyp.abschnitttyp if abschnitt.abschnitttyp else ''
        inhalt = abschnitt.inhalt or ''
        if typ == "liste ungeordnet":
            inhalt = "\n".join(["- " + line for line in inhalt.splitlines()])
            html = markdown(inhalt, extensions=['tables', 'attr_list'])
        elif typ == "liste geordnet":
            inhalt = "\n".join(["1. " + line for line in inhalt.splitlines()])
            html = markdown(inhalt, extensions=['tables', 'attr_list'])
        elif typ == "tabelle":
            html = md_table_to_html(inhalt)
        elif typ == "diagramm":
            temp = inhalt.splitlines()
            diagramtype = temp.pop(0)
            diagramoptions = 'width="100%"'
            if temp and temp[0][0:6].lower() == "option":
                diagramoptions = temp.pop(0).split(":", 1)[1]
            rest = "\n".join(temp)
            
            # Use caching instead of URL encoding
            try:
                cache_path = get_cached_diagram(diagramtype, rest)
                # Generate URL to serve from media/static
                diagram_url = settings.MEDIA_URL + cache_path
                html = f'<p><img {diagramoptions} src="{diagram_url}"></p>'
            except Exception as e:
                # Fallback to error message
                html = f'<p class="text-danger">Error generating diagram: {str(e)}</p>'
                
        elif typ == "code":
            html = "<pre><code>"
            html += markdown(inhalt, extensions=['tables', 'attr_list'])
            html += "</code></pre>"
        else:
            html = markdown(inhalt, extensions=['tables', 'attr_list','footnotes'])
        # Sanitize HTML to prevent XSS
        html = bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)
        output.append((typ, html))
    return output

def md_table_to_html(md: str) -> str:
    # 1.  Split into lines and drop empties
    lines = [ln.strip() for ln in md.splitlines() if ln.strip()]

    # 2.  Remove the separator line (|---|----|)
    if len(lines) < 2:
        raise ValueError("Need at least header + separator line")
    header_line = lines[0]
    body_lines  = lines[2:]          # skip separator

    # 3.  Parse cells ----------------------------------------------------
    def split_row(line: str):
        # Trim possible leading/trailing pipes, then split
        return [cell.strip() for cell in line.strip('|').split('|')]

    headers = split_row(header_line)
    rows    = [split_row(ln) for ln in body_lines]

    # 4.  Build HTML -----------------------------------------------------
    def wrap(tag, inner):
        return f"<{tag}>{inner}</{tag}>\n"

    thead = wrap("thead",
                 wrap("tr",
                      "".join(wrap("th", h) for h in headers)))

    tbody_rows = []
    for r in rows:
        cells = "".join(wrap("td", c) for c in r)
        tbody_rows.append(wrap("tr", cells))
    tbody = wrap("tbody", "".join(tbody_rows))

    html = f'<table class="table table-bordered table-hover">\n{thead}{tbody}</table>'
    return html
