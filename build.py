#!/usr/bin/env python3
"""
BreachWatcher static build script.

Reads alerts.json and updates three things automatically:
  - index.html               (alerts carousel)
  - security-alerts/*.html  (More Security Alerts section on each page)
  - sitemap.xml              (security-alerts <url> entries)

Usage:
    python build.py

Run this from the repo root before committing whenever you add a new alert.
To add a new alert: create the article HTML, add an entry to alerts.json, run build.py.
"""

import json
import os
import re
from html import escape

ROOT = os.path.dirname(os.path.abspath(__file__))

CAROUSEL_START = '<!-- ALERTS-CAROUSEL-START -->'
CAROUSEL_END   = '<!-- ALERTS-CAROUSEL-END -->'
MORE_START     = '<!-- MORE-ALERTS-START -->'
MORE_END       = '<!-- MORE-ALERTS-END -->'
SITEMAP_START  = '<!-- SECURITY-ALERTS-START -->'
SITEMAP_END    = '<!-- SECURITY-ALERTS-END -->'


# ── file helpers ───────────────────────────────────────────────────────────

def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def write(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def replace_section(text, start, end, new_content):
    pattern = re.compile(re.escape(start) + r'.*?' + re.escape(end), re.DOTALL)
    replacement = start + '\n' + new_content + end
    result, n = pattern.subn(replacement, text)
    if n == 0:
        raise ValueError(f'markers not found: {start!r}')
    return result

def update_file(path, start, end, new_content):
    rel = os.path.relpath(path, ROOT)
    original = read(path)
    try:
        updated = replace_section(original, start, end, new_content)
    except ValueError as e:
        print(f'  SKIP    {rel} — {e}')
        return
    if updated == original:
        print(f'  no change  {rel}')
    else:
        write(path, updated)
        print(f'  updated    {rel}')


# ── HTML / XML generators ──────────────────────────────────────────────────

def e(s):
    return escape(s, quote=False)

def build_carousel_card(a):
    tags = '\n'.join(
        f'          <span class="alert-tag {t["class"]}">{e(t["label"])}</span>'
        for t in a['tags']
    )
    return (
        f'\n'
        f'    <div class="alert-card">\n'
        f'      <div class="alert-icon"><i class="{a["icon"]}"></i></div>\n'
        f'      <div class="alert-content">\n'
        f'        <div class="alert-tags">\n'
        f'{tags}\n'
        f'        </div>\n'
        f'        <div class="alert-title">{e(a["title"])}</div>\n'
        f'        <div class="alert-desc">{e(a["description"])}</div>\n'
        f'        <div class="alert-date">'
        f'<i class="fas fa-calendar-days" style="margin-right:6px"></i>'
        f'{e(a["dateDisplay"])}</div>\n'
        f'        <a href="security-alerts/{a["slug"]}.html" class="alert-read-more">'
        f'Read more <i class="fas fa-arrow-right"></i></a>\n'
        f'      </div>\n'
        f'    </div>\n'
    )

def build_more_card(a):
    tag_text = ' · '.join(t['label'] for t in a['tags'])
    return (
        f'    <a href="{a["slug"]}.html" class="more-card">\n'
        f'      <div class="more-card-tag">{e(tag_text)}</div>\n'
        f'      <div class="more-card-title">{e(a["title"])}</div>\n'
        f'      <div class="more-card-date">{e(a["dateDisplay"])}</div>\n'
        f'    </a>\n'
    )

def build_sitemap_entry(a):
    return (
        f'  <url>\n'
        f'    <loc>https://www.breachwatcher.io/security-alerts/{a["slug"]}.html</loc>\n'
        f'    <lastmod>{a["date"]}</lastmod>\n'
        f'    <changefreq>monthly</changefreq>\n'
        f'    <priority>0.7</priority>\n'
        f'  </url>\n'
    )


# ── main ───────────────────────────────────────────────────────────────────

def main():
    with open(os.path.join(ROOT, 'alerts.json'), encoding='utf-8') as f:
        alerts = json.load(f)
    alerts.sort(key=lambda a: a['date'], reverse=True)

    # 1. index.html — carousel
    print('index.html')
    update_file(
        os.path.join(ROOT, 'index.html'),
        CAROUSEL_START, CAROUSEL_END,
        ''.join(build_carousel_card(a) for a in alerts),
    )

    # 2. security-alerts/*.html — More Security Alerts
    print('\nsecurity-alerts/')
    alerts_dir = os.path.join(ROOT, 'security-alerts')
    for filename in sorted(os.listdir(alerts_dir)):
        if not filename.endswith('.html') or filename.startswith('_'):
            continue
        slug = filename[:-5]
        others = [a for a in alerts if a['slug'] != slug]
        update_file(
            os.path.join(alerts_dir, filename),
            MORE_START, MORE_END,
            ''.join(build_more_card(a) for a in others),
        )

    # 3. sitemap.xml
    print('\nsitemap.xml')
    update_file(
        os.path.join(ROOT, 'sitemap.xml'),
        SITEMAP_START, SITEMAP_END,
        ''.join(build_sitemap_entry(a) for a in alerts),
    )

    print('\nDone.')

if __name__ == '__main__':
    main()
