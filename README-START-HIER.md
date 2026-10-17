# Wipperfürth aktuell – Version 1

Diese Website ist ein lauffähiger Prototyp für `wipp-aktuell.de`.

## Bestandteile
- Responsives Nachrichtenlayout, acht Rubriken und redaktionelle Artikelseiten
- Lokale Suche auf der Startseite bzw. innerhalb einer Rubrik (keine globale Volltextsuche)
- Artikel als JSON-Dateien unter `content/articles/`
- Pages CMS Konfiguration unter `.pages.yml`
- Instagram-Profillinks, bewusst ohne Tracking-Embeds
- Entwürfe: Artikel mit `published: false` sind auf der Website nicht sichtbar
- Impressum/Datenschutz als **nicht veröffentlichungsreife Platzhalter**
- Sitemap und Grund-Metadaten

## Benötigte Konten
1. GitHub: https://github.com/
2. Cloudflare: https://dash.cloudflare.com/
3. Pages CMS: https://app.pagescms.org/ (GitHub-Login)
4. STRATO: bestehendes Domainkonto

## Einrichten – ohne zusätzliche Hosting-Gebühren

### Schritt 1: Repository anlegen
1. Auf GitHub anmelden und ein neues Repository `wipp-aktuell-website` anlegen (für unkompliziertes kostenloses Deployment zunächst **öffentlich**; keine geheimen Daten hochladen).
2. **Alle Dateien und Ordner aus diesem Projekt** ins Repository laden, darunter die versteckte Datei `.pages.yml`. Beim Hochladen im Browser darauf achten, dass die Verzeichnisstruktur erhalten bleibt; alternativ GitHub Desktop oder Git benutzen.
3. Keine personenbezogenen Zugangsdaten oder Passwörter ins Repository schreiben.

### Schritt 2: Cloudflare Pages
1. Cloudflare Dashboard > Workers & Pages > Create > Pages > mit GitHub verbinden.
2. Das Repository `wipp-aktuell-website` auswählen.
3. Produktionsbranch `main`, Framework-Preset `None` wählen.
4. Build command: `python3 build.py`
5. Build output directory: `dist`
6. Deploy starten. Zuerst sollte eine `*.pages.dev`-Testadresse funktionieren.
7. Jeder veröffentlichte Artikel verändert das GitHub-Repository und löst damit automatisch einen neuen Build aus.

### Schritt 3: Redaktionszugang
1. https://app.pagescms.org/ öffnen und mit GitHub einloggen.
2. Pages CMS GitHub App für das Repository autorisieren/installieren.
3. Das Repository öffnen; `.pages.yml` wird erkannt.
4. Im Bereich **Nachrichtenartikel** einen Beitrag anlegen. Felder: Überschrift, Rubrik, Datum, Kurzbeschreibung, optionales Titelbild, Artikeltext, Schalter `Veröffentlichen`.
5. Änderungen speichern und den Cloudflare-Build abwarten. Neue Beiträge erscheinen erst nach erfolgreichem Build.
6. Um einen Beitrag als Entwurf zurückzuhalten: `Veröffentlichen` ausschalten.

**Wichtig:** Der redaktionelle Login erfolgt bei `app.pagescms.org`, nicht unter `wipp-aktuell.de`. Der Menüpunkt „Redaktion“ auf der Website verweist dorthin. Nur GitHub-Nutzer mit Berechtigung für das Repository dürfen bearbeiten.

### Schritt 4: STRATO-Domain
1. Erst nachdem die `pages.dev`-Testwebsite funktioniert, im Cloudflare-Pages-Projekt unter **Custom domains** die Domain `wipp-aktuell.de` hinzufügen.
2. Die Domain bei Cloudflare als Zone aufnehmen. Cloudflare zeigt zwei eigene Nameserver an.
3. **Vor** der Nameserver-Umstellung bei STRATO sämtliche bestehenden DNS-Einträge dokumentieren, insbesondere MX, SPF, DKIM, DMARC und sonstige E-Mail-Einträge, wenn E-Mail über STRATO oder einen anderen Anbieter läuft.
4. Relevante DNS-Einträge in Cloudflare übernehmen. Anschließend bei STRATO die Nameserver der Domain auf die von Cloudflare angezeigten Werte umstellen (nur wenn STRATO dies für dein Domainprodukt erlaubt).
5. Im Cloudflare Pages Projekt `www.wipp-aktuell.de` ergänzen und gewünschte Weiterleitung (www -> ohne www oder umgekehrt) konfigurieren.
6. TLS/HTTPS-Funktion und Mailzustellung prüfen. Änderungen können Zeit zur Verbreitung benötigen.

Wenn STRATO bei deinem Tarif keine Nameserveränderungen erlaubt, zuerst die mögliche Domain-/Subdomain-DNS-Konfiguration prüfen; für die Hauptdomain ist eine andere Strategie nötig. Nicht blind A-/CNAME-Einträge setzen.

### Schritt 5: Vor öffentlichem Start
- Pflichtangaben im Impressum ergänzen. Die Verantwortlichen- und Anbieterangaben können nicht automatisiert erfunden werden.
- Individuell passende Datenschutzerklärung erarbeiten. Cloudflare Hosting und die tatsächlichen Datenflüsse müssen berücksichtigt werden.
- Drei Musterartikel entfernen oder durch echte, belegte Lokalnachrichten ersetzen.
- Eigene Bildrechte und Quellenangaben prüfen, Bildbeschreibungen ergänzen.
- Falls du schon eine Website/E-Mail unter der Domain nutzt: vor Änderungen Backup erstellen.

## Lokal testen
Python 3 verwenden:

```sh
python3 build.py
cd dist
python3 -m http.server 8000
```

Dann `http://localhost:8000` öffnen. Bei Änderungen an Artikeln `python3 build.py` erneut aufrufen.

## Layout und Inhalte bearbeiten
- Design: `assets/style.css`
- Artikel: `content/articles/*.json` (oder komfortabel Pages CMS)
- Build-Generator: `build.py`
- Kategorien: Liste `CATEGORIES` in `build.py` und Auswahlwerte in `.pages.yml` gemeinsam bearbeiten.

## Kosten und Grenzen
GitHub, Pages CMS und Cloudflare Pages bieten kostenlose Einstiegsmöglichkeiten. Kosten, Freigrenzen und Bedingungen können sich ändern; Hosting ist nicht garantiert dauerhaft unbegrenzt. Die bereits bestehende STRATO-Domain bleibt kostenpflichtig. Im Grundsetup gibt es keine externen eingebetteten Social-Media-Feeds, bezahlten Plugins oder Analyse-Dienste.
