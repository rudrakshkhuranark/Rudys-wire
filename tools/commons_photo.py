#!/usr/bin/env python3
"""Find and download a freely licensed Wikimedia Commons photo for the Rudy Wire plate.
Usage: commons_photo.py "<search terms>" <out_dir>
Prints JSON candidates (title, licence, author, file) and saves up to 4 images as cand_N.jpg.
Retries politely on HTTP 429 (shared cloud IPs are often rate-limited), up to ~4 minutes."""
import json, sys, time, urllib.request, urllib.parse, urllib.error, re, os
UA = "RudyWireBot/1.0 (https://github.com/rudrakshkhuranark/rudys-wire; bot@rudywire.local)"
FREE = re.compile(r"^(CC0|CC BY(-SA)?( \d\.\d)?|Public domain|PD.*)$", re.I)
def get(url, deadline):
    wait = 5
    while True:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or time.time() > deadline: raise
            ra = e.headers.get("Retry-After")
            time.sleep(min(60, int(ra) if ra and ra.isdigit() else wait)); wait = min(60, wait * 2)
def main():
    q, out = sys.argv[1], sys.argv[2]; os.makedirs(out, exist_ok=True)
    deadline = time.time() + 240
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "generator": "search", "gsrsearch": "filetype:bitmap " + q, "gsrnamespace": 6,
        "gsrlimit": 12, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1280, "format": "json"})
    pages = json.loads(get(api, deadline)).get("query", {}).get("pages", {})
    found = []
    for p in sorted(pages.values(), key=lambda p: p.get("index", 99)):
        ii = p["imageinfo"][0]; m = ii.get("extmetadata", {})
        lic = re.sub("<[^>]+>", "", m.get("LicenseShortName", {}).get("value", "")).strip()
        if not FREE.match(lic) or ii.get("width", 0) < 600: continue
        author = re.sub("<[^>]+>", "", m.get("Artist", {}).get("value", "unknown")).strip()
        fn = os.path.join(out, f"cand_{len(found)}.jpg")
        try: open(fn, "wb").write(get(ii["thumburl"], deadline))
        except Exception as e: print(json.dumps({"skip": p["title"], "err": str(e)})); continue
        found.append({"title": p["title"], "licence": lic, "author": author[:80], "page": ii.get("descriptionurl"), "file": fn})
        if len(found) == 4: break
    print(json.dumps(found, indent=1))
main()
