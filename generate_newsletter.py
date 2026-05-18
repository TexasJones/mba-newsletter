"""
MBA Newsletter Generator — 100% Free Version
Uses RSS feeds from Google News and other free sources.
No API keys, no accounts, no cost.
Runs via GitHub Actions every Monday and saves an HTML file.
"""

import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from html import escape

# ── RSS Feed Sources per Topic ────────────────────────────────────────────────
# Google News RSS supports any search query — completely free, no key needed.

TOPICS = [
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
        "label": "MBA for Working Professionals & Career Coaching",
        "color": "#be185d",
        "bg": "#fdf2f8",
        "border": "#fbcfe8",
        "icon": "💼",
        "feeds": [
            "https://news.google.com/rss/search?q=MBA+working+professional+career+coaching&hl=en-US&gl=US&ceid=US:en",
            "https://news.google.com/rss/search?q=part+time+MBA+working+professional+career&hl=en-US&gl=US&ceid=US:en",
        ],
    },
]

# ── RSS Fetching ──────────────────────────────────────────────────────────────

def clean_html(raw: str) -> str:
    """Strip HTML tags from a string."""
    return re.sub(r"<[^>]+>", "", raw or "").strip()


def fetch_feed(url: str, max_items: int = 5) -> list[dict]:
    """Fetch and parse an RSS feed, returning a list of article dicts."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
    except Exception as e:
        print(f"    ⚠ Could not fetch {url[:60]}... ({e})")
        return []

    articles = []
    # Handle both RSS <item> and Atom <entry> formats
    items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

    for item in items[:max_items]:
        def get(tag):
            el = item.find(tag)
            if el is None:
                el = item.find(f"{{http://www.w3.org/2005/Atom}}{tag}")
            return (el.text or "").strip() if el is not None else ""

        title = clean_html(get("title"))
        link = get("link") or get("guid")
        description = clean_html(get("description") or get("summary"))
        pub_date = get("pubDate") or get("published") or get("updated")

        # Parse and format the date nicely
        formatted_date = ""
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z",
                    "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
            try:
                dt = datetime.strptime(pub_date.strip(), fmt)
                formatted_date = dt.strftime("%b %d, %Y")
                break
            except ValueError:
                continue

        # Skip items with no title or link
        if not title or not link:
            continue

        # Truncate description to ~200 chars
        if len(description) > 220:
            description = description[:217].rsplit(" ", 1)[0] + "…"

        # Extract source name from Google News titles (format: "Headline - Source")
        source = ""
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0].strip()
            source = parts[1].strip()

        articles.append({
            "title": title,
            "url": link,
            "description": description,
            "source": source,
            "date": formatted_date,
        })

    return articles


def fetch_topic(topic: dict, max_per_feed: int = 4) -> list[dict]:
    """Fetch articles for a topic from all its feeds, deduplicated."""
    print(f"  Fetching: {topic['label']}...")
    seen_titles = set()
    results = []
    for feed_url in topic["feeds"]:
        for article in fetch_feed(feed_url, max_per_feed):
            key = article["title"].lower()[:60]
            if key not in seen_titles:
                seen_titles.add(key)
                results.append(article)
        if len(results) >= 6:
            break
    print(f"    → {len(results)} articles found")
    return results[:6]


# ── HTML Generation ───────────────────────────────────────────────────────────

def article_card_html(article: dict, color: str) -> str:
    title_escaped = escape(article["title"])
    desc_escaped = escape(article["description"]) if article["description"] else ""
    url = escape(article["url"])
    source = escape(article["source"]) if article["source"] else ""
    date = escape(article["date"]) if article["date"] else ""

    meta_parts = []
    if source:
        meta_parts.append(f'<span style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;letter-spacing:0.07em;font-family:monospace;">{source}</span>')
    if date:
        meta_parts.append(f'<span style="font-size:11px;color:#94a3b8;">{date}</span>')
    if url:
        meta_parts.append(f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="font-size:12px;color:{color};text-decoration:none;font-weight:700;" onmouseover="this.style.opacity=\'0.7\'" onmouseout="this.style.opacity=\'1\'">Read article →</a>')

    meta_html = ' <span style="color:#e2e8f0;">·</span> '.join(meta_parts)

    return f"""
    <div style="background:#fff;border:1px solid #e2e8f0;border-left:4px solid {color};
         border-radius:8px;padding:16px 18px;margin-bottom:12px;transition:box-shadow 0.2s;"
         onmouseover="this.style.boxShadow='0 4px 14px rgba(0,0,0,0.09)';this.style.background='#f8fafc'"
         onmouseout="this.style.boxShadow='none';this.style.background='#fff'">
      <div style="font-size:15px;font-weight:700;margin-bottom:6px;line-height:1.45;">
        <a href="{url}" target="_blank" rel="noopener noreferrer"
           style="color:{color};text-decoration:none;"
           onmouseover="this.style.textDecoration='underline'"
           onmouseout="this.style.textDecoration='none'">{title_escaped}</a>
      </div>
      {"<p style='font-size:13.5px;color:#475569;margin:0 0 10px;line-height:1.65;'>" + desc_escaped + "</p>" if desc_escaped else ""}
      <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
        {meta_html}
      </div>
    </div>"""


def topic_section_html(topic: dict, articles: list[dict]) -> str:
    count = f'{len(articles)} article{"s" if len(articles) != 1 else ""} found'
    if articles:
        cards = "".join(article_card_html(a, topic["color"]) for a in articles)
    else:
        cards = '<p style="text-align:center;color:#94a3b8;font-size:13px;padding:20px 0;">No articles found this week.</p>'

    return f"""
  <div style="margin-bottom:44px;">
    <div style="display:flex;align-items:center;gap:12px;background:{topic["bg"]};
         border:1px solid {topic["border"]};border-radius:10px;padding:14px 20px;margin-bottom:18px;">
      <span style="font-size:24px;">{topic["icon"]}</span>
      <div>
        <div style="font-size:16px;font-weight:800;color:{topic["color"]};font-family:Georgia,serif;">
          {escape(topic["label"])}
        </div>
        <div style="font-size:12px;color:#64748b;margin-top:2px;">{count}</div>
      </div>
    </div>
    {cards}
  </div>"""


def build_html(results: list[dict], generated_at: str) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    total = sum(len(r["articles"]) for r in results)
    sections = "".join(topic_section_html(r["topic"], r["articles"]) for r in results)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>The MBA Insider – {today}</title>
  <style>
    * {{ box-sizing: border-box; }}
    body {{ margin:0; padding:0; background:#f1f5f9; font-family:Georgia,'Times New Roman',serif; }}
    a {{ cursor:pointer; }}
    @media (max-width:600px) {{ .main {{ padding:20px !important; }} }}
  </style>
</head>
<body>
  <div style="max-width:740px;margin:36px auto;padding:0 16px 60px;">

    <!-- Masthead -->
    <div style="background:#0f172a;border-radius:14px 14px 0 0;padding:36px 36px 28px;text-align:center;">
      <div style="font-size:10px;font-family:monospace;color:#64748b;letter-spacing:0.2em;text-transform:uppercase;margin-bottom:12px;">
        Weekly Intelligence Brief
      </div>
      <h1 style="margin:0 0 8px;font-size:36px;font-weight:900;color:#f8fafc;letter-spacing:-0.02em;line-height:1.1;">
        The MBA Insider
      </h1>
      <div style="font-size:13px;color:#64748b;margin-bottom:20px;letter-spacing:0.04em;">
        Career Coaching · Career Advising · Artificial Intelligence
      </div>
      <div style="display:inline-block;background:rgba(255,255,255,0.07);border:1px solid rgba(255,255,255,0.1);
           border-radius:6px;padding:6px 16px;font-size:12px;color:#cbd5e1;font-family:monospace;">
        {today}
      </div>
    </div>

    <!-- Body -->
    <div class="main" style="background:#fff;border-radius:0 0 14px 14px;
         box-shadow:0 8px 32px rgba(0,0,0,0.08);padding:36px;">

      <!-- Stats bar -->
      <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:28px;padding:14px 18px;
           background:#f8fafc;border-radius:8px;border:1px solid #e2e8f0;">
        <span style="font-size:13px;color:#475569;">📰 <strong>{total} articles</strong> curated</span>
        <span style="font-size:13px;color:#94a3b8;">·</span>
        <span style="font-size:13px;color:#475569;">🗂 <strong>{len(results)} topics</strong> covered</span>
        <span style="font-size:13px;color:#94a3b8;">·</span>
        <span style="font-size:13px;color:#475569;">🕐 Generated {generated_at}</span>
      </div>

      <div style="border-top:1px solid #e2e8f0;margin-bottom:36px;"></div>

      {sections}

      <!-- Footer -->
      <div style="border-top:2px solid #0f172a;padding-top:20px;margin-top:8px;text-align:center;">
        <div style="font-size:12px;color:#94a3b8;line-height:1.8;">
          <strong style="color:#475569;">The MBA Insider</strong> · Auto-generated weekly newsletter · {today}<br/>
          Powered by Google News RSS feeds · Click any headline to read the full article.<br/>
          <span style="color:#cbd5e1;">100% free · No API keys · Runs on GitHub Actions</span>
        </div>
      </div>

    </div>
  </div>
</body>
</html>"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("📰 MBA Newsletter Generator (Free RSS Edition)")
    print(f"   Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"   Topics: {len(TOPICS)}\n")

    results = []
    for topic in TOPICS:
        articles = fetch_topic(topic)
        results.append({"topic": topic, "articles": articles})

    generated_at = datetime.now().strftime("%I:%M %p UTC, %B %d %Y")
    html = build_html(results, generated_at)

    import os
    os.makedirs("newsletters", exist_ok=True)

    dated_file = f"newsletters/mba-insider-{datetime.now().strftime('%Y-%m-%d')}.html"
    latest_file = "newsletters/latest.html"

    with open(dated_file, "w", encoding="utf-8") as f:
        f.write(html)
    with open(latest_file, "w", encoding="utf-8") as f:
        f.write(html)

    total = sum(len(r["articles"]) for r in results)
    print(f"\n✅ Done! {total} articles saved.")
    print(f"   Dated file : {dated_file}")
    print(f"   Latest file: {latest_file}")


if __name__ == "__main__":
    main()
