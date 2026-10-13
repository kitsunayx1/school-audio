"""Build feed.xml and README.md from episodes.json.

Episodes are grouped by week (iTunes season = week number). Within a week the
summary comes first, then one deep dive per reading.
"""
import json, os, subprocess
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = "https://raw.githubusercontent.com/kitsunayx1/school-audio/main/"


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout
    s = int(float(out.strip()))
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


data = json.load(open(os.path.join(ROOT, "episodes.json")))
items, readme = [], []
for wk in sorted(data["weeks"], key=lambda w: w["week"]):
    base_time = datetime.fromisoformat(wk["date"]).replace(hour=12, tzinfo=timezone.utc)
    readme.append(f"\n## Week {wk['week']}\n")
    n = len(wk["episodes"])
    for i, ep in enumerate(wk["episodes"]):
        rel = f"{wk['folder']}/{ep['file']}"
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            continue
        # Earlier episodes in a week get later timestamps so "newest first" apps show the summary on top.
        pub = base_time + timedelta(minutes=n - i)
        items.append(f"""    <item>
      <title>{escape(ep['title'])}</title>
      <description>{escape(ep['description'])}</description>
      <enclosure url="{BASE}{rel}" length="{os.path.getsize(path)}" type="audio/mpeg"/>
      <guid isPermaLink="false">{rel}</guid>
      <pubDate>{format_datetime(pub)}</pubDate>
      <itunes:duration>{duration(path)}</itunes:duration>
      <itunes:season>{wk['week']}</itunes:season>
      <itunes:episode>{i + 1}</itunes:episode>
    </item>""")
        readme.append(f"- [{ep['title']}]({rel}) ({duration(path)})")

feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
  <channel>
    <title>NSEC506 Study Audio</title>
    <link>https://github.com/kitsunayx1/school-audio</link>
    <description>Weekly reading summaries and per-reading deep dives for NSEC506. AI-narrated study notes, not the original texts.</description>
    <language>en-us</language>
    <itunes:author>NSEC506 Study Audio</itunes:author>
    <itunes:image href="{BASE}cover.jpg"/>
    <itunes:explicit>false</itunes:explicit>
    <itunes:type>episodic</itunes:type>
    <itunes:category text="Education"/>
{chr(10).join(reversed(items))}
  </channel>
</rss>
"""
open(os.path.join(ROOT, "feed.xml"), "w").write(feed)

open(os.path.join(ROOT, "README.md"), "w").write(f"""# NSEC506 Study Audio

AI-narrated study notes for NSEC506 readings, sorted by week. Each week has one summary episode covering all readings, then a deep dive per reading. These are paraphrased study notes, not recordings of the original texts.

**Podcast feed:** `{BASE}feed.xml`

Add that URL in any podcast app that supports adding a show by URL (Pocket Casts, Overcast, Apple Podcasts via Library > Follow a Show by URL).
{chr(10).join(readme)}

To add a week: drop MP3s in `weekNN/`, add entries to `episodes.json`, run `python3 tools/build_feed.py`.
""")
print(len(items), "episodes")
