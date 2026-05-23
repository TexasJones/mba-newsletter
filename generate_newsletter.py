"""
Chris's MBA Insider News — Daily Newsletter Generator
100% Free: Google News RSS feeds + GitHub Actions
No API keys, no accounts, no cost.
"""

import os
import re
import smtplib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape, unescape

# ── Brand colors ──────────────────────────────────────────────────────────────
BRAND = {
    "primary":    "#BF5700",
    "primary_dk": "#8B3E00",
    "primary_lt": "#F8EDE3",
    "accent":     "#333F48",
    "bg":         "#FAF7F4",
}

# ── Topics ────────────────────────────────────────────────────────────────────
TOPICS = [
    {
        "id": "mccombs",
        "label": "McCombs MBA",
        "color": "#BF5700",
        "bg": "#FDF0E8",
        "border": "#F4C6A0",
        "icon": "🤘",
        "feeds": [
            "https://news.google.com/rss/search?q=McCombs+MBA&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=McCombs+School+of+Business+UT+Austin&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "coaching",
        "label": "MBA & Career Coaching",
        "color": "#1d4ed8",
        "bg": "#eff6ff",
        "border": "#bfdbfe",
        "icon": "🎓",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+career+coaching&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=business+school+career+coaching&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "advising",
        "label": "MBA & Career Advising",
        "color": "#0f766e",
        "bg": "#f0fdfa",
        "border": "#99f6e4",
        "icon": "🧭",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+career+advising&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=graduate+school+career+advising&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "ai",
        "label": "MBA & Artificial Intelligence",
        "color": "#7c3aed",
        "bg": "#f5f3ff",
        "border": "#ddd6fe",
        "icon": "🤖",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+artificial+intelligence&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=business+school+AI+education&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "aicoaching",
        "label": "AI in Career Coaching & Advising",
        "color": "#b45309",
        "bg": "#fffbeb",
        "border": "#fde68a",
        "icon": "⚡",
        "feeds": [
            "https://news.google.com/rss/search?q=AI+career+coaching+advising&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=artificial+intelligence+career+development&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "workingpro",
        "label": "MBA for Working Professionals",
        "color": "#be185d",
        "bg": "#fdf2f8",
        "border": "#fbcfe8",
        "icon": "💼",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+working+professional+career+coaching&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=part+time+MBA+working+professional+career&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "execed",
        "label": "MBA & Executive Education",
        "color": "#0369a1",
        "bg": "#f0f9ff",
        "border": "#bae6fd",
        "icon": "🏛️",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+executive+education&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=executive+MBA+program+trends&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "roi",
        "label": "MBA Return on Investment",
        "color": "#15803d",
        "bg": "#f0fdf4",
        "border": "#bbf7d0",
        "icon": "📈",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+return+on+investment+salary&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=MBA+worth+it+ROI+2026&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "online",
        "label": "MBA Online Programs",
        "color": "#0891b2",
        "bg": "#ecfeff",
        "border": "#a5f3fc",
        "icon": "💻",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+online+programs+2026&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=online+MBA+rankings+trends&hl=en-US&gl=US&ceid=US:en",
        ],
    },
    {
        "id": "networking",
        "label": "MBA & Networking",
        "color": "#6d28d9",
        "bg": "#f5f3ff",
        "border": "#c4b5fd",
        "icon": "🤝",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+networking+career&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=business+school+alumni+networking&hl=en-US&gl=US&ceid=US:en",
        ],
    },
]

# ── RSS Fetching ──────────────────────────────────────────────────────────────

def clean_html(raw):
    text = re.sub(r"<[^>]+>", "", raw or "")
    return unescape(text).strip()

def fetch_feed(url, max_items=5):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"    ⚠ Could not fetch {url[:60]}... ({e})")
        return []

    articles = []
    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for item in items[:max_items]:
        def get(tag):
            el = item.find(tag)
            if el is None:
                el = item.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
            return (el.text or "").strip() if el is not None else ""

        title       = clean_html(get("title"))
        link        = get("link") or get("guid")
        description = clean_html(get("description") or get("summary"))
        pub_date    = get("pubDate") or get("published") or get("updated")

        formatted_date = ""
        sort_dt = None
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                dt = datetime.strptime(pub_date.strip(), fmt)
                formatted_date = dt.strftime("%b %d, %Y")
                sort_dt = dt
                break
            except ValueError:
                continue

        if not title or not link:
            continue
        if len(description) > 220:
            description = description[:217].rsplit(" ", 1)[0] + "…"

        source = ""
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title  = parts[0].strip()
            source = parts[1].strip()

        articles.append({
            "title": title, "url": link, "description": description,
            "source": source, "date": formatted_date, "sort_dt": sort_dt,
        })
    return articles

def fetch_topic(topic, max_per_feed=4):
    print(f"  Fetching: {topic['label']}...")
    seen, results = set(), []
    for feed_url in topic["feeds"]:
        for article in fetch_feed(feed_url, max_per_feed):
            key = article["title"].lower()[:60]
            if key not in seen:
                seen.add(key)
                results.append(article)
        if len(results) >= 6:
            break
    # Sort newest first
    results.sort(
        key=lambda a: a["sort_dt"].replace(tzinfo=None) if a["sort_dt"] else datetime.min,
        reverse=True
    )
    print(f"    → {len(results)} articles found")
    return results[:6]

# ── HTML Generation ───────────────────────────────────────────────────────────

def article_card_html(article, color, topic_id):
    t  = escape(article["title"])
    d  = escape(article["description"]) if article["description"] else ""
    u  = escape(article["url"])
    s  = escape(article["source"]) if article["source"] else ""
    dt = escape(article["date"])   if article["date"]   else ""

    meta_parts = []
    if s:
        meta_parts.append(f'<span style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;font-family:monospace;">{s}</span>')
    if dt:
        meta_parts.append(f'<span style="font-size:11px;color:#94a3b8;">{dt}</span>')
    if u:
        meta_parts.append(f'<a href="{u}" target="_blank" rel="noopener noreferrer" style="font-size:12px;color:{color};text-decoration:none;font-weight:700;" onmouseover="this.style.opacity=\'0.7\'" onmouseout="this.style.opacity=\'1\'">Read article →</a>')
    meta_html = ' <span style="color:#e2e8f0;">·</span> '.join(meta_parts)
    desc_html = f'<p style="font-size:13.5px;color:#475569;margin:0 0 10px;line-height:1.65;">{d}</p>' if d else ""

    return f"""<div class="article-card" data-topic="{topic_id}" data-text="{t.lower()} {s.lower()} {d.lower()}"
     style="background:#fff;border:1px solid #e8e0d8;border-left:4px solid {color};border-radius:8px;
            padding:16px 18px;margin-bottom:12px;transition:all 0.2s ease;"
     onmouseover="this.style.background='#faf7f4';this.style.boxShadow='0 4px 14px rgba(191,87,0,0.1)'"
     onmouseout="this.style.background='#fff';this.style.boxShadow='none'">
  <div style="font-size:15px;font-weight:700;margin-bottom:6px;line-height:1.45;">
    <a href="{u}" target="_blank" rel="noopener noreferrer"
       style="color:{color};text-decoration:none;"
       onmouseover="this.style.textDecoration='underline'"
       onmouseout="this.style.textDecoration='none'">{t}</a>
  </div>
  {desc_html}
  <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">{meta_html}</div>
</div>"""

def toc_html(results):
    links = []
    for r in results:
        t = r["topic"]
        count = len(r["articles"])
        links.append(
            f'<a href="#{t["id"]}" style="display:inline-flex;align-items:center;gap:6px;'
            f'background:{t["bg"]};border:1px solid {t["border"]};color:{t["color"]};'
            f'border-radius:20px;padding:6px 14px;font-size:12px;font-weight:600;'
            f'text-decoration:none;white-space:nowrap;">'
            f'{t["icon"]} {escape(t["label"])} '
            f'<span style="background:{t["color"]};color:#fff;border-radius:10px;padding:1px 7px;font-size:11px;">{count}</span></a>'
        )
    return '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:32px;">' + "".join(links) + '</div>'

def topic_section_html(topic, articles):
    count = f'{len(articles)} article{"s" if len(articles) != 1 else ""} found'
    cards = "".join(article_card_html(a, topic["color"], topic["id"]) for a in articles) if articles else \
        '<p style="text-align:center;color:#94a3b8;font-size:13px;padding:20px 0;">No articles found today.</p>'
    return f"""<div id="{topic['id']}" style="margin-bottom:44px;">
  <div style="display:flex;align-items:center;gap:12px;background:{topic["bg"]};
       border:1px solid {topic["border"]};border-radius:10px;padding:14px 20px;margin-bottom:18px;">
    <span style="font-size:24px;">{topic["icon"]}</span>
    <div>
      <div style="font-size:16px;font-weight:800;color:{topic["color"]};font-family:Georgia,serif;">
        {escape(topic["label"])}
      </div>
      <div style="font-size:12px;color:#64748b;margin-top:2px;">{count} · sorted by date</div>
    </div>
    <a href="#top" style="margin-left:auto;font-size:11px;color:#94a3b8;text-decoration:none;"
       onmouseover="this.style.color='#BF5700'" onmouseout="this.style.color='#94a3b8'">↑ Top</a>
  </div>
  {cards}
</div>"""

def build_html(results, generated_at):
    today    = datetime.now().strftime("%B %d, %Y")
    total    = sum(len(r["articles"]) for r in results)
    sections = "".join(topic_section_html(r["topic"], r["articles"]) for r in results)
    toc      = toc_html(results)
    all_cards = "\n".join(
        article_card_html(a, r["topic"]["color"], r["topic"]["id"])
        for r in results for a in r["articles"]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>Chris's MBA Insider News – {today}</title>
  <style>
    *{{box-sizing:border-box;}}
    body{{margin:0;padding:0;background:#FAF7F4;font-family:Georgia,'Times New Roman',serif;}}
    a{{cursor:pointer;}}
    #search-box{{width:100%;padding:12px 18px 12px 44px;font-size:14px;border:2px solid #e8e0d8;
      border-radius:8px;font-family:Georgia,serif;outline:none;background:#fff;transition:border-color 0.2s;}}
    #search-box:focus{{border-color:#BF5700;}}
    .search-wrap{{position:relative;margin-bottom:24px;}}
    .search-icon{{position:absolute;left:14px;top:50%;transform:translateY(-50%);font-size:16px;pointer-events:none;}}
    @media(max-width:600px){{.main{{padding:20px !important;}} h1{{font-size:26px !important;}}}}
  </style>
</head>
<body>
<div id="top" style="max-width:760px;margin:32px auto;padding:0 16px 60px;">

  <!-- Masthead -->
  <div style="background:linear-gradient(135deg,#8B3E00 0%,#BF5700 60%,#D4621A 100%);
       border-radius:16px 16px 0 0;padding:40px 36px 32px;text-align:center;position:relative;overflow:hidden;">
    <div style="position:absolute;top:-40px;right:-40px;width:180px;height:180px;border-radius:50%;background:rgba(255,255,255,0.05);"></div>
    <div style="position:absolute;bottom:-60px;left:-30px;width:220px;height:220px;border-radius:50%;background:rgba(255,255,255,0.04);"></div>
    <div style="position:relative;">
      <div style="font-size:10px;font-family:monospace;color:rgba(255,255,255,0.5);letter-spacing:0.25em;text-transform:uppercase;margin-bottom:14px;">
        Daily Intelligence Brief
      </div>
      <h1 style="margin:0 0 6px;font-size:38px;font-weight:900;color:#fff;letter-spacing:-0.02em;line-height:1.1;text-shadow:0 2px 8px rgba(0,0,0,0.2);">
        Chris's MBA Insider News
      </h1>
      <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:22px;letter-spacing:0.05em;">
        McCombs · Career Coaching · Advising · AI · Executive Ed · Networking
      </div>
      <div style="display:inline-flex;align-items:center;gap:16px;flex-wrap:wrap;justify-content:center;">
        <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:6px;padding:7px 18px;font-size:12px;color:#fff;font-family:monospace;">
          📅 {today}
        </div>
        <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:6px;padding:7px 18px;font-size:12px;color:#fff;font-family:monospace;">
          📰 {total} articles · {len(results)} topics
        </div>
        <div style="background:rgba(255,255,255,0.12);border:1px solid rgba(255,255,255,0.2);border-radius:6px;padding:7px 18px;font-size:12px;color:#fff;font-family:monospace;">
          🕐 {generated_at}
        </div>
      </div>
    </div>
  </div>

  <!-- Body -->
  <div class="main" style="background:#fff;border-radius:0 0 16px 16px;box-shadow:0 8px 40px rgba(191,87,0,0.1);padding:36px;">

    <!-- Search -->
    <div class="search-wrap">
      <span class="search-icon">🔍</span>
      <input id="search-box" type="text" placeholder="Search all articles by keyword, source, or topic…" oninput="filterArticles(this.value)"/>
    </div>

    <!-- TOC -->
    <div id="toc-section">
      <div style="font-size:11px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:10px;">Jump to section</div>
      {toc}
    </div>

    <div style="border-top:2px solid #F8EDE3;margin-bottom:36px;"></div>

    <!-- Search results (hidden by default) -->
    <div id="search-results" style="display:none;">
      <div style="font-size:13px;color:#64748b;margin-bottom:16px;">
        Results for: <strong id="search-term" style="color:#BF5700;"></strong>
        <span id="result-count" style="color:#94a3b8;margin-left:8px;"></span>
      </div>
      <div id="search-cards">{all_cards}</div>
      <div id="no-results-msg" style="display:none;text-align:center;color:#94a3b8;padding:32px;font-size:14px;">No articles found matching your search.</div>
    </div>

    <!-- Topic sections -->
    <div id="topic-sections">{sections}</div>

    <!-- Footer -->
    <div style="border-top:3px solid #BF5700;padding-top:22px;margin-top:8px;text-align:center;">
      <div style="font-size:13px;font-weight:800;color:#BF5700;margin-bottom:4px;">Chris's MBA Insider News</div>
      <div style="font-size:12px;color:#94a3b8;line-height:1.9;">
        Auto-generated daily · {today} · {generated_at}<br/>
        Powered by Google News RSS · Articles sorted by date · Click any headline to read the original.<br/>
        <span style="color:#cbd5e1;">100% free · No API keys · Runs automatically on GitHub Actions</span>
      </div>
    </div>
  </div>
</div>

<script>
  const allCards = document.querySelectorAll('#search-cards .article-card');
  function filterArticles(query) {{
    const q = query.trim().toLowerCase();
    const topicSections = document.getElementById('topic-sections');
    const searchResults = document.getElementById('search-results');
    const tocSection    = document.getElementById('toc-section');
    const searchTerm    = document.getElementById('search-term');
    const resultCount   = document.getElementById('result-count');
    const noResults     = document.getElementById('no-results-msg');
    if (!q) {{
      topicSections.style.display = 'block';
      searchResults.style.display = 'none';
      tocSection.style.display    = 'block';
      return;
    }}
    topicSections.style.display = 'none';
    tocSection.style.display    = 'none';
    searchResults.style.display = 'block';
    searchTerm.textContent = query;
    let visible = 0;
    allCards.forEach(card => {{
      const match = (card.getAttribute('data-text') || '').includes(q);
      card.style.display = match ? 'block' : 'none';
      if (match) visible++;
    }});
    resultCount.textContent  = visible > 0 ? `(${{visible}} article${{visible !== 1 ? 's' : ''}})` : '';
    noResults.style.display  = visible === 0 ? 'block' : 'none';
  }}
</script>
</body>
</html>"""

# ── Email Notification ────────────────────────────────────────────────────────

def send_email():
    gmail     = os.environ.get("GMAIL_ADDRESS", "")
    app_pw    = os.environ.get("GMAIL_APP_PASSWORD", "")
    recipient = os.environ.get("RECIPIENT_EMAIL") or gmail

    if not gmail or not app_pw:
        print("\n⚠ Email skipped — GMAIL_ADDRESS or GMAIL_APP_PASSWORD not set.")
        return

    today = datetime.now().strftime("%B %d, %Y")
    url   = "https://texasjones.github.io/mba-newsletter/newsletters/latest.html"

    print(f"\n📧 Sending from: {gmail}")
    print(f"📬 Sending to:   {recipient}")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Chris's MBA Insider News is ready - {today}"
    msg["From"]    = f"MBA Insider <{gmail}>"
    msg["To"]      = recipient

    text_body = f"Chris's MBA Insider News - {today}\n\nRead it here: {url}\n\nAuto-generated daily."
    html_body = f"""<html><body style="font-family:Georgia,serif;background:#FAF7F4;padding:32px;">
  <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;">
    <div style="background:linear-gradient(135deg,#8B3E00,#BF5700);padding:28px 32px;text-align:center;">
      <h1 style="margin:0;font-size:24px;color:#fff;font-weight:900;">Chris's MBA Insider News</h1>
      <div style="font-size:12px;color:rgba(255,255,255,0.65);margin-top:8px;">{today}</div>
    </div>
    <div style="padding:28px 32px;text-align:center;">
      <p style="font-size:15px;color:#475569;line-height:1.7;margin:0 0 24px;">
        Your daily MBA newsletter is ready with the latest articles on McCombs,
        career coaching, advising, AI, executive education, networking, and more.
      </p>
      <a href="{url}" style="display:inline-block;background:#BF5700;color:#fff;
              text-decoration:none;font-size:15px;font-weight:700;padding:14px 32px;border-radius:8px;">
        Read Today's Newsletter
      </a>
      <p style="font-size:12px;color:#94a3b8;margin-top:20px;">
        <a href="{url}" style="color:#BF5700;">{url}</a>
      </p>
    </div>
  </div>
</body></html>"""

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        print("🔌 Connecting to smtp.gmail.com:465...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            print("🔐 Logging in...")
            server.login(gmail, app_pw)
            print("📤 Sending...")
            server.sendmail(gmail, recipient, msg.as_string())
        print(f"✅ Email sent to {recipient}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Auth failed: {e}")
    except Exception as e:
        print(f"❌ Email error: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("📰 Chris's MBA Insider News Generator")
    print(f"   Date:   {datetime.now().strftime('%B %d, %Y')}")
    print(f"   Topics: {len(TOPICS)}\n")

    results = []
    for topic in TOPICS:
        articles = fetch_topic(topic)
        results.append({"topic": topic, "articles": articles})

    generated_at = datetime.now().strftime("%I:%M %p UTC")
    html = build_html(results, generated_at)

    os.makedirs("newsletters", exist_ok=True)
    dated  = f"newsletters/mba-insider-{datetime.now().strftime('%Y-%m-%d')}.html"
    latest = "newsletters/latest.html"

    for path in (dated, latest):
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    total = sum(len(r["articles"]) for r in results)
    print(f"\n✅ Done! {total} articles across {len(TOPICS)} topics.")
    print(f"   Dated : {dated}")
    print(f"   Latest: {latest}")

    send_email()

if __name__ == "__main__":
    main()
