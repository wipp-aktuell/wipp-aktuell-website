#!/usr/bin/env python3
"""Build an independent static German local-news site; stdlib only."""
import json, re, html, shutil, pathlib, datetime, unicodedata
from urllib.parse import quote, urlsplit
from zoneinfo import ZoneInfo
ROOT=pathlib.Path(__file__).resolve().parent
DIST=ROOT/'dist'
ARTICLES=ROOT/'content'/'articles'
ADS = ROOT / 'content' / 'ads'
COMPANIES = ROOT / 'content' / 'companies'
CATEGORIES=['Aktuelles','Blaulicht','Verkehr','Politik','Wirtschaft','Veranstaltungen','Sport','Stadtgeschichte']

def news_article_jsonld(article):
    url = 'https://wipp-aktuell.de/artikel/' + article['slug'] + '/'

    data = {
        '@context': 'https://schema.org',
        '@type': 'NewsArticle',
        'mainEntityOfPage': {
            '@type': 'WebPage',
            '@id': url
        },
        'headline': article.get('title', ''),
        'description': article.get('summary', ''),
        'datePublished': article.get('date', ''),
        'author': {
            '@type': 'Organization',
            'name': 'Wipperfürth aktuell'
        },
        'publisher': {
            '@type': 'Organization',
            'name': 'Wipperfürth aktuell',
            'url': 'https://wipp-aktuell.de/'
        }
    }

    image = article.get('cover', '')
    if image:
        if image.startswith('/'):
            image = 'https://wipp-aktuell.de' + image
        data['image'] = image

    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace('<', '\\u003c')

    return '<script type="application/ld+json">' + payload + '</script>'

def esc(s): return html.escape(str(s or ''),quote=True)
def safe_ad_url(value):
    value = str(value or '').strip()

    if not value:
        return ''

    try:
        parsed = urlsplit(value)

        if parsed.scheme not in ('https', 'http'):
            return ''

        if not parsed.hostname:
            return ''

        if parsed.username or parsed.password:
            return ''

        return value

    except ValueError:
        return ''
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
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)} | Wipperfürth aktuell</title><meta name="description" content="{esc(description)}">{canonical_tag}<meta name="theme-color" content="#09243d"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:type" content="{'article' if article else 'website'}"><link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="/assets/style.css?v=20261018-2"></head><body><div class="topline"><div class="wrap"><span>Dein Nachrichtenportal für die Hansestadt</span><a href="https://www.instagram.com/wipp_aktuell/" target="_blank" rel="noopener noreferrer">Instagram: @wipp_aktuell ↗</a></div></div><header class="masthead"><div class="wrap masthead-inner"><a href="/" aria-label="Wipperfürth aktuell Startseite">
<div class="brand-with-logo"><img class="site-logo" src="/assets/logo-wipp-aktuell.jpg" alt="Logo von Wipperfürth aktuell"><div class="brand">Wipperfürth <strong>aktuell.</strong></div></div>
<div class="brand-sub">Lokal. Unabhängig. Informiert.</div></a><div class="social"><a href="/redaktion/">Redaktion</a><a class="red-link" target="_blank" rel="noopener noreferrer" href="https://www.instagram.com/wipp_aktuell/">Instagram ↗</a></div></div></header><nav class="nav" aria-label="Rubriken"><div class="wrap nav-inner"><a href="/" class="{'active' if not active else ''}">
Startseite</a>{nav}<a href="/unternehmen/" class="{'active' if canonical.startswith('/unternehmen/') else ''}">Unternehmen</a>
<a href="/werbung/" class="{'active' if canonical == '/werbung/' else ''}">Werbung schalten</a>
</div></nav>{content}<footer class="footer"><div class="wrap footer-inner"><div><h3>Wipperfürth aktuell.</h3><p>Lokale Nachrichten und Geschichten aus Wipperfürth. Unabhängiges, nichtamtliches Nachrichtenangebot.</p></div><div><a href="/impressum/">Impressum</a><a href="/datenschutz/">Datenschutz</a><a href="https://www.instagram.com/wipp_aktuell/" target="_blank" rel="noopener noreferrer">Instagram ↗</a></div></div></footer><script src="/assets/app.js" defer></script></body></html>'''
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


def render_news_with_ads(articles, ads=None):
    ads = ads or []
    parts = []
    ad_index = 0

    for index, article in enumerate(articles):
        parts.append(card(article))

        if (index + 1) % 4 == 0 and ad_index < len(ads):
            parts.append(render_ad(ads[ad_index]))
            ad_index += 1

    # Verbleibende Anzeigen auch bei wenigen Artikeln anzeigen
    while ad_index < len(ads):
        parts.append(render_ad(ads[ad_index]))
        ad_index += 1

    return ''.join(parts)



def sidebar():
    tags=''.join(f'<a class="tag" href="/rubrik/{slug(c)}/">{esc(c)}</a>' for c in CATEGORIES)
    return f'''<aside class="sidebar"><section class="sidebox"><h3>Auf Instagram</h3><p>Weitere Meldungen, Eindrücke und Beiträge findest du auf unserem offiziellen Instagram-Profil.</p><a class="button" target="_blank" rel="noopener noreferrer" href="https://www.instagram.com/wipp_aktuell/">@wipp_aktuell öffnen ↗</a></section><section class="sidebox"><h3>Unsere Rubriken</h3><div class="taglist">{tags}</div></section><section class="sidebox"><h3>Hinweis senden</h3><p>Du hast eine lokale Nachricht oder einen Veranstaltungshinweis? Schreib uns gern über Instagram.</p><a class="button" href="https://www.instagram.com/wipp_aktuell/" target="_blank" rel="noopener noreferrer">Kontakt über Instagram ↗</a></section></aside>'''
def render_ad(ad):
    company = esc(ad.get('company', ''))
    description = esc(ad.get('description', ''))
    image = ad.get('image') or ''
    image_alt = esc(ad.get('image_alt') or company)
    target = safe_ad_url(ad.get('target_url'))
    
    image_html = ''
    if (
        isinstance(image, str)
        and image.startswith('/uploads/')
        and '..' not in image
    ):
        image_html = (
            '<img class="ad-image" loading="lazy" src="'
            + esc(image) + '" alt="' + image_alt + '">'
        )

    content = (
        '<div class="ad-content">'
        + image_html
        + '<div class="ad-text">'
        + '<strong class="ad-company">' + company + '</strong>'
        + ('<p>' + description + '</p>' if description else '')
        + '</div></div>'
    )

    if target:
        content = (
            '<a class="ad-link" href="' + esc(target)
            + '" target="_blank" rel="sponsored noopener noreferrer">'
            + content + '</a>'
        )

    return (
        '<aside class="advertisement" aria-label="Werbung">'
        '<div class="ad-label">Anzeige</div>'
        + content
        + '</aside>'
    )
def ad_is_active(ad, today):
    if not ad.get('active', False):
        return False

    start = str(ad.get('start_date') or '')[:10]
    end = str(ad.get('end_date') or '')[:10]

    if not start or not end:
        return False

    return start <= today <= end


def check_ad_bookings(ads):
    limits = {
        'Premium-Startseite': 1,
        'Standard-Startseite': 3,
    }

    bookings = {}

    
    for ad in ads:
        status = ad.get('booking_status', '')

        if status not in ('Reserviert', 'Bestätigt'):
            continue


        placement = ad.get('placement', '')
        category = ad.get('category', '')

        if placement == 'Rubrikensponsor':
            if not category:
                continue
            key = (placement, category)
            limit = 1
        elif placement in limits:
            key = (placement, '')
            limit = limits[placement]
        else:
            continue

        try:
            start = datetime.date.fromisoformat(
                str(ad.get('start_date', ''))[:10]
            )
            end = datetime.date.fromisoformat(
                str(ad.get('end_date', ''))[:10]
            )
        
        except (ValueError, TypeError):
            print(
                'WARNUNG: Ungueltiges Buchungsdatum:',
                ad.get('title')
            )
            continue


        if end < start:
            print('WARNUNG: Enddatum vor Startdatum:', ad.get('title'))
            continue

        bookings.setdefault(key, []).append(
            (start, end, ad.get('title', 'Ohne Namen'), limit)
        )

    for key, entries in bookings.items():
        events = []

        for start, end, title, limit in entries:
            events.append((start, 1, title))
            events.append((end + datetime.timedelta(days=1), -1, title))

        events.sort(key=lambda event: event[0])

        count = 0
        warned = False

        for date, change, title in events:
            count += change

            if count > entries[0][3] and not warned:
                print(
                    'WARNUNG: Werbeplatz ueberbucht:',
                    key,
                    'ab',
                    date.isoformat()
                )
                warned = True



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


def listing(title,description,arr,home=False,premium_ad='',standard_ads=None):
    hero=f'<div class="hero"><div class="wrap"><div class="eyebrow">Nachrichten für Wipperfürth</div><h1>Was unsere Stadt bewegt.</h1><p>Aktuelle Nachrichten, Hintergründe und Geschichten aus Wipperfürth – übersichtlich an einem Ort.</p></div></div>' if home else f'<div class="hero"><div class="wrap"><div class="eyebrow">Wipperfürth aktuell</div><h1>{esc(title)}</h1><p>{esc(description)}</p></div></div>'
    text=f'<div class="cards">{render_news_with_ads(arr, standard_ads)}</div>' if arr or standard_ads else '<div class="empty">In dieser Rubrik sind noch keine Artikel veröffentlicht.</div>'
    return hero+premium_ad+f'''<main class="wrap layout"><section><div class="section-heading"><h2>{'Neueste Beiträge' if home else esc(title)}</h2><small>{len(arr)} Beiträge</small></div><label for="search" class="sr-only">Artikel durchsuchen</label><div class="searchbar"><input id="search" type="search" placeholder="Artikel durchsuchen …" aria-label="Artikel durchsuchen"><button type="button" onclick="document.querySelector('#search').value='';document.querySelector('#search').dispatchEvent(new Event('input'))">Zurücksetzen</button></div>{text}<p class="empty" id="no-results" hidden>Keine passenden Artikel gefunden.</p></section>{sidebar()}</main>'''
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

    companies = []

    if COMPANIES.exists():
        for file in COMPANIES.glob('*.json'):
            data = json.loads(
                file.read_text(encoding='utf-8')
            )

            if not data.get('published', False):
                continue

            if not data.get('title'):
                continue

            data['slug'] = slug(file.stem)
            companies.append(data)

    companies.sort(
        key=lambda company: company.get('title', '').lower()
    )

    print(f'Unternehmensvorstellungen eingelesen: {len(companies)}')


    print(f'Werbeanzeigen eingelesen: {len(ads)}')
    check_ad_bookings(ads)
    today = datetime.datetime.now(ZoneInfo('Europe/Berlin')).date().isoformat()
    premium_ads = select_ads(ads, 'Premium-Startseite', today)
    premium_html = render_ad(premium_ads[0]) if premium_ads else ''
    standard_ads = select_ads(ads, 'Standard-Startseite', today)[:3]
    write(pathlib.Path('index.html'),base('Nachrichten aus Wipperfürth','Aktuelle Nachrichten, Stadtleben und Hintergründe aus Wipperfürth.',listing('Aktuelles','',articles,True,premium_ad=premium_html,standard_ads=standard_ads)
,canonical='/'))
    for cat in CATEGORIES:
        selected=[a for a in articles if a['category']==cat]
        sponsor_ads = select_ads(ads, 'Rubrikensponsor', today, category=cat)
        sponsor_html = render_ad(sponsor_ads[0]) if sponsor_ads else ''
        write(pathlib.Path('rubrik')/slug(cat)/'index.html',base(cat,'Nachrichten und Informationen aus der Rubrik '+cat,
listing(cat,'Meldungen und Hintergründe aus Wipperfürth.',selected,premium_ad=sponsor_html)
,active=cat,canonical='/rubrik/'+slug(cat)+'/'))
    for a in articles:
        article=f'''<main class="wrap layout"><article class="article"><div class="pill">{esc(a['category'])}</div><h1>{esc(a['title'])}</h1><div class="meta">Veröffentlicht am {prettydate(a.get('date',''))}</div><p class="article-lead">{esc(a.get('summary',''))}</p>
{cover(a, show_credit=True)}
<div class="article-content">{md(a.get('body',''))}</div>{'<div class="notice">Quelle: '+esc(a['source'])+'</div>' if a.get('source') else ''}<p><a class="button" href="/">← Zurück zur Startseite</a></p></article>{sidebar()}</main>'''
        
        article = article + news_article_jsonld(a)
        write(pathlib.Path('artikel')/a['slug']/'index.html',base(a['title'],a.get('summary',''),article,active=a['category'],canonical='/artikel/'+a['slug']+'/',article=True))
    
    for company in companies:
        company_title = esc(company.get('title', ''))
        company_name = esc(company.get('company', ''))
        company_category = esc(company.get('category', ''))
        company_summary = esc(company.get('summary', ''))
        company_body = md(company.get('body', ''))

        company_image = company.get('cover') or ''
        company_image_html = ''

        if (
            isinstance(company_image, str)
            and company_image.startswith('/uploads/')
            and '..' not in company_image
        ):
            image_alt = esc(
                company.get('image_alt') or company.get('title', '')
            )
            image_credit = esc(company.get('image_credit') or '')

            company_image_html = (
                '<figure class="article-figure">'
                '<div class="cover"><img loading="lazy" src="'
                + esc(company_image)
                + '" alt="' + image_alt + '"></div>'
                + (
                    '<figcaption class="image-credit">Foto: '
                    + image_credit + '</figcaption>'
                    if image_credit else ''
                )
                + '</figure>'
            )

        company_url = safe_ad_url(company.get('website'))
        company_link = ''

        if company_url:
            company_link = (
                '<p><a class="button" href="' + esc(company_url)
                + '" target="_blank" rel="sponsored noopener noreferrer">'
                'Unternehmenswebsite besuchen</a></p>'
            )

        company_html = (
            '<main class="wrap layout">'
            '<article class="article">'
            '<div class="pill">Anzeige · Unternehmensvorstellung</div>'
            '<h1>' + company_title + '</h1>'
            '<p class="article-lead">' + company_summary + '</p>'
            + company_image_html
            + '<div class="article-content">'
            + '<p><strong>Unternehmen:</strong> ' + company_name + '</p>'
            + '<p><strong>Branche:</strong> ' + company_category + '</p>'
            + company_body
            + company_link
            + '</div></article>'
            + sidebar()
            + '</main>'
        )

        write(
            pathlib.Path('unternehmen') / company['slug'] / 'index.html',
            base(
                company.get('title', ''),
                company.get('summary', ''),
                company_html,
                canonical='/unternehmen/' + company['slug'] + '/'
            )
        )

    write(pathlib.Path('redaktion')/'index.html',base('Redaktion','Geschützter Redaktionszugang', '''<main class="legal"><h1>Redaktionsbereich</h1><p>Beiträge werden über Pages CMS geschrieben, bearbeitet und veröffentlicht. Der Login erfolgt sicher mit deinem GitHub-Konto.</p><p><a class="button" href="https://app.pagescms.org/" rel="noopener noreferrer" target="_blank">Zum Redaktionsbereich ↗</a></p><p><strong>Hinweis:</strong> Der Redaktionsbereich liegt bei Pages CMS und nicht auf dieser Website. Nur berechtigte GitHub-Konten können Inhalte bearbeiten.</p></main>''',canonical='/redaktion/'))
    
    company_cards = []

    for company in companies:
        title = esc(company.get('title', ''))
        name = esc(company.get('company', ''))
        category = esc(company.get('category', ''))
        summary = esc(company.get('summary', ''))
        url = '/unternehmen/' + company['slug'] + '/'

        image_html = ''
        image = company.get('cover') or ''

        if (
            isinstance(image, str)
            and image.startswith('/uploads/')
            and '..' not in image
        ):
            image_html = (
                '<img loading="lazy" src="' + esc(image)
                + '" alt="' + esc(company.get('image_alt') or title)
                + '">'
            )

        company_cards.append(
            '<a class="company-card" href="' + esc(url) + '">'
            '<div class="company-card-label">Anzeige</div>'
            + image_html
            + '<div class="company-card-content">'
            + '<small>' + category + '</small>'
            + '<h2>' + title + '</h2>'
            + '<strong>' + name + '</strong>'
            + '<p>' + summary + '</p>'
            + '</div></a>'
        )

    company_overview = (
        '<main class="wrap">'
        '<section class="company-overview">'
        '<h1>Unternehmen aus Wipperfürth</h1>'
        '<p class="article-lead">'
        'Bezahlte Unternehmensvorstellungen aus Wipperfürth '
        'und Umgebung. Alle Einträge sind Werbung.'
        '</p>'
        '<div class="company-grid">'
        + (
            ''.join(company_cards)
            if company_cards
            else '<p>Derzeit sind keine Unternehmensvorstellungen veröffentlicht.</p>'
        )
        + '</div></section></main>'
    )

    write(
        pathlib.Path('unternehmen') / 'index.html',
        base(
            'Unternehmen aus Wipperfürth',
            'Bezahlte Unternehmensvorstellungen aus Wipperfürth.',
            company_overview,
            canonical='/unternehmen/'
        )
    )


    werbung_html = '''
    <main class="wrap">
      <section class="company-overview">
        <p class="pill">Werben bei Wipperfürth aktuell</p>
        <h1>Werben, wo Wipperfürth liest.</h1>
        <p class="article-lead">
          Präsentieren Sie Ihr Unternehmen auf unserem lokalen
          Nachrichtenportal. Wir bieten Werbemöglichkeiten für
          Gastronomie, Einzelhandel, Handwerk, Dienstleister
          und weitere Unternehmen aus Wipperfürth und Umgebung.
        </p>

        <div class="company-grid">
          <div class="company-card">
            <div class="company-card-content">
              <h2>Premium-Banner</h2>
              <p>Prominente Platzierung auf unserer Startseite,
              oberhalb der neuesten Nachrichten.</p>
            </div>
          </div>

          <div class="company-card">
            <div class="company-card-content">
              <h2>Standard-Anzeigen</h2>
              <p>Ihre Werbung zwischen den Nachrichten
              auf unserer Startseite.</p>
            </div>
          </div>

          <div class="company-card">
            <div class="company-card-content">
              <h2>Rubrikensponsoring</h2>
              <p>Werbung in einem passenden Themenbereich,
              beispielsweise Verkehr, Sport oder Wirtschaft.</p>
            </div>
          </div>

          <div class="company-card">
            <div class="company-card-content">
              <h2>Unternehmensvorstellungen</h2>
              <p>Ein eigener, als Anzeige gekennzeichneter Beitrag
              über Ihr Unternehmen und seine Angebote.</p>
            </div>
          </div>

          <div class="company-card">
            <div class="company-card-content">
              <h2>Instagram & Website</h2>
              <p>Fragen Sie nach einem individuellen Kombiangebot
              mit unserem Instagram-Kanal @wipp_aktuell.</p>
            </div>
          </div>
        </div>

        <section class="sidebar-box" style="margin-top:32px">
          <h2>Jetzt Werbeanfrage stellen</h2>
          <p>
            Sie möchten Ihr Unternehmen bei Wipperfürth aktuell
            präsentieren? Wir erstellen Ihnen gerne ein
            individuelles Angebot.
          </p>
          <p>
            <a class="button"
               href="mailto:info@wipp-aktuell.de?subject=Werbeanfrage%20Wipperfuerth%20aktuell">
              Werbeanfrage per E-Mail senden
            </a>
          </p>
          <p>
            E-Mail: <strong>info@wipp-aktuell.de</strong>
          </p>
        </section>
      </section>
    </main>
    '''

    write(
        pathlib.Path('werbung') / 'index.html',
        base(
            'Werbung schalten',
            'Werbemöglichkeiten für Unternehmen aus Wipperfürth.',
            werbung_html,
            canonical='/werbung/'
        )
    )


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

    links = (
        ['/', '/impressum/', '/datenschutz/', '/unternehmen/', '/werbung/']
        + [f'/rubrik/{slug(c)}/' for c in CATEGORIES]
        + [f'/artikel/{a["slug"]}/' for a in articles]
    )

    write(pathlib.Path('sitemap.xml'),'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join(f'<url><loc>https://wipp-aktuell.de{esc(p)}</loc></url>' for p in links)+'</urlset>')
    print(f'Built {len(articles)} posts, {len(links)} URLs in {DIST}')
if __name__=='__main__':main()
