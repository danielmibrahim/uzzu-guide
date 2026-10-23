#!/usr/bin/env python3
"""Turn Uzzu's JSON TV guide into an XMLTV file TiviMate can read.

Uzzu's playlist gives every channel a tvg-id (e.g. "espn.us") and a stream URL ending in
"<number>.m3u8"; its guide at <playlist URL>/epg is JSON keyed by that same number. This joins
the two, so each programme is filed under the tvg-id TiviMate already knows the channel by.

Usage: UZZU_URL=https://uzzu.tv/hls/<your id> python3 make_guide.py out.xml.gz
The output contains only channel names and listings, never the playlist URL or account id.
"""
import gzip, json, os, re, sys, urllib.request
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape, quoteattr

UA = {"User-Agent": "TiviMate/5.3.3"}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return r.read().decode("utf-8")


def xmltv_time(iso):
    return datetime.fromisoformat(iso).strftime("%Y%m%d%H%M%S %z")


def main():
    base = os.environ["UZZU_URL"].rstrip("/")
    out = sys.argv[1] if len(sys.argv) > 1 else "uzzu.xml.gz"

    # stream number -> (tvg-id, name); a few Uzzu channels share a tvg-id, the first one keeps it
    channels, seen = {}, set()
    for info, url in re.findall(r"#EXTINF:[^\n]*?(tvg-id=\"[^\"]*\"[^\n]*)\n(\S+)", fetch(base)):
        num = re.search(r"/(\d+)\.m3u8$", url)
        tid = re.search(r'tvg-id="([^"]*)"', info).group(1)
        if num and tid and tid not in seen:
            seen.add(tid)
            channels[num.group(1)] = (tid, info.rsplit(",", 1)[-1].strip())

    # Uzzu sends 24h by default; asking for 48h (all it has) gives TiviMate a day of slack between updates
    until = (datetime.now(timezone.utc) + timedelta(hours=48)).strftime("%Y-%m-%dT%H:00:00%%2B00:00")
    guide = json.loads(fetch(f"{base}/epg?to={until}"))["data"] or {}
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<tv generator-info-name="uzzu-guide">']
    used = [n for n in guide if n in channels]
    for n in used:
        tid, name = channels[n]
        lines.append(f"  <channel id={quoteattr(tid)}><display-name>{escape(name)}</display-name></channel>")
    count = 0
    for n in used:
        tid = channels[n][0]
        for p in guide[n]:
            lines.append(f'  <programme start="{xmltv_time(p["start"])}" stop="{xmltv_time(p["end"])}" channel={quoteattr(tid)}>')
            lines.append(f'    <title>{escape(p.get("title") or "")}</title>')
            if p.get("description"):
                lines.append(f'    <desc>{escape(p["description"])}</desc>')
            if p.get("category"):
                lines.append(f'    <category>{escape(p["category"])}</category>')
            lines.append("  </programme>")
            count += 1
    lines.append("</tv>")

    if count == 0:
        sys.exit("No programmes matched; keeping the previous guide")
    with gzip.open(out, "wt", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{len(used)} channels, {count} programmes -> {out}")


if __name__ == "__main__":
    main()
