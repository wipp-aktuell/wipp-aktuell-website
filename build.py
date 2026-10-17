#!/usr/bin/env python3
"""Build an independent static German local-news site; stdlib only."""
import json, re, html, shutil, pathlib, datetime, unicodedata
from urllib.parse import quote
ROOT=pathlib.Path(__file__).resolve().parent
DIST=ROOT/'dist'
ARTICLES=ROOT/'content'/'articles'
ADS = ROOT / 'content' / 'ads'
CATEGORIES=['Aktuelles','Blaulicht','Verkehr','Politik','Wirtschaft','Veranstaltungen','Sport','Stadtgeschichte']
def esc(s): return html.escape(str(s or ''),quote=True)
def slug(s):
    s=unicodedata.normalize('NFKD',str(s).lower()).replace('ß','ss')
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'(^-|-$)','',re.sub(r'[^a-z0-9]+','-',s)) or 'artikel'
def prettydate(d):
    try:return datetime.date.fromisoformat(str(d)[:10]).strftime('%d.%m.%Y')
    except: return esc(d)
def md(text):
    # Render a restricted Markdown subset safely, without allowing raw HTML.
    text=html.escape(text or '')
    text=re.sub(r'!\[([^]]*)\]\((/uploads/[\w./-]+)\)',lambda m:'<img loading="lazy" alt="'+esc(html.unescape(m[1]))+'" src="'+m[2]+'">',text)
    text=re.sub(r'\[([^]]+)\]\((https?://[^\s)]+)\)',lambda m:'<a rel="noopener noreferrer" target="_blank" href="'+m[2]+'">'+m[1]+'</a>',text)
    text=re.sub(r'\*\*([^*\n]+)\*\*',r'<strong>\1</strong>',text)
    text=re.sub(r'(?<!\*)\*([^*\n]+)\*(?!\*)',r'<em>\1</em>',text)
    blocks=[]
    for block in re.split(r'\n\s*\n',text.strip()):
        if not block:continue
        if block.startswith('## '): blocks.append('<h2>'+block[3:]+'</h2>')
        else:blocks.append('<p>'+block.replace('\n','<br>')+'</p>')
    return '\n'.join(blocks)
def base(title,description,content,active='',canonical='',article=False):
    nav=''.join(f'<a href="/rubrik/{slug(cat)}/" class="{"active" if cat==active else ""}">{esc(cat)}</a>' for cat in CATEGORIES)
    canonical_tag=f'<link rel="canonical" href="https://wipp-aktuell.de{esc(canonical)}">' if canonical else ''
    return f'''<!doctype html><html lang="de">
<head><link rel="icon" type="image/jpeg" href="/assets/logo-wipp-aktuell.jpg">
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | Wipperfürth aktuell</title><meta name="description" content="{esc(description)}">{canonical_tag}<meta name="theme-color" content="#09243d"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="{'article' if article else 'website'}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css"></head><body><div class="topline"><div class="wrap"><span>Dein Nachrichtenportal für die Hansestadt</span><a href="https://www.instagram.com/wipp_aktuell/" target="_blank" rel="noopener noreferrer">Instagram: @wipp_aktuell ↗</a></div></div><header class="masthead"><div class="wrap masthead-inner"><a href="/" aria-label="Wipperfürth aktuell Startseite">
<div class="brand-with-logo"><img class="site-logo" src="/assets/logo-wipp-aktuell.jpg" alt="Logo von Wipperfürth aktuell"><div class="brand">Wipperfürth <strong>aktuell.</strong></div></div>
<div class="brand-sub">Lokal. Unabhängig. Informiert.</div></a><div class="social"><a href="/redaktion/">Redaktion</a><a class="red-link" target="_blank" rel="noopener noreferrer" href="https://www.instagram.com/wipp_aktuell/">Instagram ↗</a></div></div></header><nav class="nav" aria-label="Rubriken"><div class="wrap nav-inner"><a href="/" class="{'active' if not active else ''}">Startseite</a>{nav}</div></nav>{content}<footer class="footer"><div class="wrap footer-inner"><div><h3>Wipperfürth aktuell.</h3><p>Lokale Nachrichten und Geschichten aus Wipperfürth. Unabhängiges, nichtamtliches Nachrichtenangebot.</p></div><div><a href="/impressum/">Impressum</a><a href="/datenschutz/">Datenschutz</a><a href="https://www.instagram.com/wipp_aktuell/" target="_blank" rel="noopener noreferrer">Instagram ↗</a></div></div></footer><script src="/assets/app.js" defer></script></body></html>'''
def write(path,txt):
    p=DIST/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(txt,encoding='utf-8')

def cover(a, show_credit=False):
    img = a.get('cover', '')
    if isinstance(img, str) and img.startswith('/uploads/') and '..' not in img:
        alt = esc(a.get('image_alt') or a['title'])
        credit = a.get('image_credit', '')
        credit_html = (
            '<figcaption class="image-credit">Foto: ' + esc(credit) + '</figcaption>'
            if credit and show_credit else ''
        )
        return (
            '<figure class="article-figure">'
            '<div class="cover"><img loading="lazy" src="' + esc(img) +
            '" alt="' + alt + '"></div>'
            + credit_html +
            '</figure>'
        )
    return '<div class="cover">Wipperfürth aktuell</div>'

def card(a):
    return f'''<a class="story" data-search="{esc((a['title']+' '+a.get('summary','')+' '+a['category']).lower())}" href="/artikel/{a['slug']}/">{cover(a)}<div class="story-body"><span class="pill">{esc(a['category'])}</span><h3>{esc(a['title'])}</h3><p>{esc(a.get('summary',''))}</p><div class="meta">{prettydate(a.get('date',''))} · weiterlesen →</div></div></a>'''
def sidebar():
    tags=''.join(f'<a class="tag" href="/rubrik/{slug(c)}/">{esc(c)}</a>' for c in CATEGORIES)
    return f'''<aside class="sidebar"><section class="sidebox"><h3>Auf Instagram</h3><p>Weitere Meldungen, Eindrücke und Beiträge findest du auf unserem offiziellen Instagram-Profil.</p><a class="button" target="_blank" rel="noopener noreferrer" href="https://www.instagram.com/wipp_aktuell/">@wipp_aktuell öffnen ↗</a></section><section class="sidebox"><h3>Unsere Rubriken</h3><div class="taglist">{tags}</div></section><section class="sidebox"><h3>Hinweis senden</h3><p>Du hast eine lokale Nachricht oder einen Veranstaltungshinweis? Schreib uns gern über Instagram.</p><a class="button" href="https://www.instagram.com/wipp_aktuell/" target="_blank" rel="noopener noreferrer">Kontakt über Instagram ↗</a></section></aside>'''

def ad_is_active(ad, today):
    if not ad.get('active', False):
        return False

    start = str(ad.get('start_date') or '')[:10]
    end = str(ad.get('end_date') or '')[:10]

    if not start or not end:
        return False

    return start <= today <= end


def select_ads(ads, placement, today, category=None):
    selected = []

    for ad in ads:
        if not ad_is_active(ad, today):
            continue

        if ad.get('placement') != placement:
            continue

        if placement == 'Rubrikensponsor':
            if ad.get('category') != category:
                continue

        selected.append(ad)

    return sorted(
        selected,
        key=lambda ad: ad.get('priority') or 1,
        reverse=True
    )


def listing(title,description,arr,home=False):
    hero=f'<div class="hero"><div class="wrap"><div class="eyebrow">Nachrichten für Wipperfürth</div><h1>Was unsere Stadt bewegt.</h1><p>Aktuelle Nachrichten, Hintergründe und Geschichten aus Wipperfürth – übersichtlich an einem Ort.</p></div></div>' if home else f'<div class="hero"><div class="wrap"><div class="eyebrow">Wipperfürth aktuell</div><h1>{esc(title)}</h1><p>{esc(description)}</p></div></div>'
    text=f'<div class="cards">{"".join(card(a) for a in arr)}</div>' if arr else '<div class="empty">In dieser Rubrik sind noch keine Artikel veröffentlicht.</div>'
    return hero+f'''<main class="wrap layout"><section><div class="section-heading"><h2>{'Neueste Beiträge' if home else esc(title)}</h2><small>{len(arr)} Beiträge</small></div><label for="search" class="sr-only">Artikel durchsuchen</label><div class="searchbar"><input id="search" type="search" placeholder="Artikel durchsuchen …" aria-label="Artikel durchsuchen"><button type="button" onclick="document.querySelector('#search').value='';document.querySelector('#search').dispatchEvent(new Event('input'))">Zurücksetzen</button></div>{text}<p class="empty" id="no-results" hidden>Keine passenden Artikel gefunden.</p></section>{sidebar()}</main>'''
def main():
    if DIST.exists():shutil.rmtree(DIST)
    shutil.copytree(ROOT/'assets',DIST/'assets')
    if (ROOT/'public').exists():shutil.copytree(ROOT/'public',DIST,dirs_exist_ok=True)
    articles=[];used=set()
    for file in ARTICLES.glob('*.json'):
        data=json.loads(file.read_text(encoding='utf-8'))
        if not data.get('published',False):continue
        if not data.get('title'):continue
        data['category']=data.get('category','Aktuelles')
        data['slug']=slug(file.stem)
        if data['slug'] in used:raise ValueError('Duplicate article slug: '+data['slug'])
        used.add(data['slug']);articles.append(data)
    articles.sort(key=lambda a:(str(a.get('date','')),a['slug']),reverse=True)
    ads = []

    if ADS.exists():
        for file in ADS.glob('*.json'):
            data = json.loads(
                file.read_text(encoding='utf-8')
            )
            ads.append(data)

    print(f'Werbeanzeigen eingelesen: {len(ads)}')
    write(pathlib.Path('index.html'),base('Nachrichten aus Wipperfürth','Aktuelle Nachrichten, Stadtleben und Hintergründe aus Wipperfürth.',listing('Aktuelles','',articles,True),canonical='/'))
    for cat in CATEGORIES:
        selected=[a for a in articles if a['category']==cat]
        write(pathlib.Path('rubrik')/slug(cat)/'index.html',base(cat,'Nachrichten und Informationen aus der Rubrik '+cat,listing(cat,'Meldungen und Hintergründe aus Wipperfürth.',selected),active=cat,canonical='/rubrik/'+slug(cat)+'/'))
    for a in articles:
        article=f'''<main class="wrap layout"><article class="article"><div class="pill">{esc(a['category'])}</div><h1>{esc(a['title'])}</h1><div class="meta">Veröffentlicht am {prettydate(a.get('date',''))}</div><p class="article-lead">{esc(a.get('summary',''))}</p>
{cover(a, show_credit=True)}
<div class="article-content">{md(a.get('body',''))}</div>{'<div class="notice">Quelle: '+esc(a['source'])+'</div>' if a.get('source') else ''}<p><a class="button" href="/">← Zurück zur Startseite</a></p></article>{sidebar()}</main>'''
        write(pathlib.Path('artikel')/a['slug']/'index.html',base(a['title'],a.get('summary',''),article,active=a['category'],canonical='/artikel/'+a['slug']+'/',article=True))
    write(pathlib.Path('redaktion')/'index.html',base('Redaktion','Geschützter Redaktionszugang', '''<main class="legal"><h1>Redaktionsbereich</h1><p>Beiträge werden über Pages CMS geschrieben, bearbeitet und veröffentlicht. Der Login erfolgt sicher mit deinem GitHub-Konto.</p><p><a class="button" href="https://app.pagescms.org/" rel="noopener noreferrer" target="_blank">Zum Redaktionsbereich ↗</a></p><p><strong>Hinweis:</strong> Der Redaktionsbereich liegt bei Pages CMS und nicht auf dieser Website. Nur berechtigte GitHub-Konten können Inhalte bearbeiten.</p></main>''',canonical='/redaktion/'))
    
    impressum_html = '''
    <main class="legal">
      <h1>Impressum</h1>

      <h2>Angaben gemäß § 5 DDG</h2>
      <p style="line-height:1.4; margin:0 0 12px 0;">
        Unternehmensberatung Andres<br>
        Inhaber: Christian Andres<br>
        Einzelunternehmen<br>
        Neusser Str. 478<br>
        50733 Köln<br>
        Deutschland
      </p>

      <h2>Kontakt</h2>
      <p style="line-height:1.4; margin:0 0 12px 0;">
        E-Mail: info@wipp-aktuell.de
      </p>

      <h2>Redaktionell verantwortlich gemäß § 18 Abs. 2 MStV</h2>
      <p style="line-height:1.4; margin:0 0 12px 0;">
        Christian Andres<br>
        Neusser Str. 478<br>
        50733 Köln<br>
        Deutschland
      </p>
    </main>
    '''
    write(
        pathlib.Path('impressum') / 'index.html',
        base(
            'Impressum',
            'Impressum von Wipperfürth aktuell',
            impressum_html,
            canonical='/impressum/'
        )
    )

    
    datenschutz_html = (ROOT / 'datenschutz.html').read_text(encoding='utf-8')
    write(
        pathlib.Path('datenschutz') / 'index.html',
        base(
            'Datenschutz',
            'Datenschutzerklärung von Wipperfürth aktuell',
            datenschutz_html,
            canonical='/datenschutz/'
        )
    )

    write(pathlib.Path('robots.txt'),'User-agent: *\nAllow: /\nSitemap: https://wipp-aktuell.de/sitemap.xml\n')
    links=['/','/redaktion/','/impressum/','/datenschutz/']+[f'/rubrik/{slug(c)}/' for c in CATEGORIES]+[f'/artikel/{a["slug"]}/' for a in articles]
    write(pathlib.Path('sitemap.xml'),'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>https://wipp-aktuell.de{esc(p)}</loc></url>' for p in links)+'</urlset>')
    print(f'Built {len(articles)} posts, {len(links)} URLs in {DIST}')
if __name__=='__main__':main()
