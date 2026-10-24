import csv
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

from make_thumb import make_thumb

API = "https://graph.instagram.com/v21.0"
TZ = ZoneInfo("America/New_York")
CSV_PATH = Path("posts.csv")
DRY_RUN = os.environ.get("DRY_RUN") == "1"
IG_USER_ID = os.environ.get("IG_USER_ID", "")
TOKEN = os.environ.get("IG_TOKEN", "")
IMAGE_BASE_URL = os.environ.get("IMAGE_BASE_URL", "").rstrip("/")
# raw.githubusercontent.com serves .mp4 as application/octet-stream, so videos come from GitHub Pages.
VIDEO_BASE_URL = os.environ.get("VIDEO_BASE_URL", "").rstrip("/") or IMAGE_BASE_URL

MAX_CAPTION = 2200
MAX_HASHTAGS = 30
MAX_CAROUSEL = 10
FIELDS = ["date", "headline", "subline", "caption", "image", "posted", "media_id", "permalink"]


def load_rows():
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_rows(rows):
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        # Keep any extra columns, but always write the standard ones (older CSVs lack permalink).
        fields = FIELDS + [k for k in rows[0] if k not in FIELDS]
        w = csv.DictWriter(f, fieldnames=fields, restval="")
        w.writeheader()
        w.writerows(rows)


def git_push(msg):
    subprocess.run(["git", "config", "user.name", "ig-autopost"], check=True)
    subprocess.run(["git", "config", "user.email", "ig-autopost@users.noreply.github.com"], check=True)
    subprocess.run(["git", "add", "-A"], check=True)
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        return
    subprocess.run(["git", "commit", "-m", msg], check=True)
    # Retry with a rebase in case you edited posts.csv on GitHub while the job ran.
    for _ in range(3):
        if subprocess.run(["git", "push"]).returncode == 0:
            return
        subprocess.run(["git", "pull", "--rebase"], check=True)
    sys.exit("git push failed 3 times")


def api(method, path, **params):
    params["access_token"] = TOKEN
    if method == "GET":
        r = requests.get(f"{API}/{path}", params=params, timeout=60)
    else:
        r = requests.post(f"{API}/{path}", data=params, timeout=60)
    if not r.ok:
        sys.exit(f"Instagram API error on {path}: {r.status_code} {r.text}")
    return r.json()


def validate(row):
    caption = row["caption"]
    if len(caption) > MAX_CAPTION:
        sys.exit(f"{row['date']}: caption is {len(caption)} chars, Instagram allows {MAX_CAPTION}")
    tags = caption.count("#")
    if tags > MAX_HASHTAGS:
        sys.exit(f"{row['date']}: caption has {tags} hashtags, Instagram allows {MAX_HASHTAGS}")


def image_files(row):
    files = [p.strip() for p in row["image"].split("|") if p.strip()]
    if len(files) > MAX_CAROUSEL:
        sys.exit(f"{row['date']}: {len(files)} images, a carousel allows {MAX_CAROUSEL}")
    if any(is_video(f) for f in files) and len(files) > 1:
        sys.exit(f"{row['date']}: a Reel is a single .mp4, don't mix it with other files")
    return files


def is_video(path):
    return path.lower().endswith(".mp4")


def wait_until_public(url, tries=20):
    for _ in range(tries):
        r = requests.head(url, timeout=15)
        if r.status_code == 200:
            return
        time.sleep(15)
    sys.exit(f"Image never became public: {url}")


def wait_until_ready(creation_id, tries=30):
    for _ in range(tries):
        status = api("GET", creation_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            sys.exit(f"Instagram rejected media {creation_id}")
        time.sleep(5)
    sys.exit(f"Media {creation_id} never finished processing")


def already_published(caption):
    """Guards against double posting if a previous run published but failed to save."""
    recent = api("GET", f"{IG_USER_ID}/media", fields="id,caption", limit=10).get("data", [])
    for m in recent:
        if (m.get("caption") or "").strip() == caption.strip():
            return m["id"]
    return None


def publish(image_urls, caption):
    if is_video(image_urls[0]):
        creation_id = api("POST", f"{IG_USER_ID}/media", media_type="REELS", video_url=image_urls[0],
                          caption=caption, share_to_feed="true")["id"]
        wait_until_ready(creation_id, tries=120)  # videos take minutes to process
        return api("POST", f"{IG_USER_ID}/media_publish", creation_id=creation_id)["id"]
    if len(image_urls) == 1:
        creation_id = api("POST", f"{IG_USER_ID}/media", image_url=image_urls[0], caption=caption)["id"]
    else:
        children = []
        for url in image_urls:
            child = api("POST", f"{IG_USER_ID}/media", image_url=url, is_carousel_item="true")["id"]
            wait_until_ready(child)
            children.append(child)
        creation_id = api("POST", f"{IG_USER_ID}/media", media_type="CAROUSEL",
                          children=",".join(children), caption=caption)["id"]
    wait_until_ready(creation_id)
    return api("POST", f"{IG_USER_ID}/media_publish", creation_id=creation_id)["id"]


def main():
    if not DRY_RUN and not (IG_USER_ID and TOKEN and IMAGE_BASE_URL):
        sys.exit("Set IG_USER_ID, IG_TOKEN and IMAGE_BASE_URL (or DRY_RUN=1)")

    rows = load_rows()
    today = datetime.now(TZ).date().isoformat()
    due = [r for r in rows if r["date"] <= today and r["posted"].strip().lower() != "yes"]
    if not due:
        print(f"Nothing due on {today}.")
        return
    row = due[0]
    validate(row)

    files = image_files(row)
    if not files:
        files = [f"posts/{row['date']}.jpg"]
        row["image"] = files[0]
    missing = [f for f in files if not Path(f).exists()]
    if missing == [f"posts/{row['date']}.jpg"]:
        make_thumb(row["headline"], row["subline"], missing[0])
        if not DRY_RUN:
            save_rows(rows)
            git_push(f"thumbnail for {row['date']}")
    elif missing:
        sys.exit(f"{row['date']}: image files not found: {missing}")

    image_urls = [f"{VIDEO_BASE_URL if is_video(f) else IMAGE_BASE_URL}/{f}" for f in files]
    print(f"Posting {row['date']}: {image_urls}")
    if DRY_RUN:
        print("DRY_RUN on, skipping Instagram.")
        return

    media_id = already_published(row["caption"])
    if media_id:
        print(f"Already on Instagram as {media_id}, just marking it posted.")
    else:
        for url in image_urls:
            wait_until_public(url)
        media_id = publish(image_urls, row["caption"])
        print(f"Published media {media_id}")

    row["posted"] = "yes"
    row["media_id"] = media_id
    row["permalink"] = api("GET", media_id, fields="permalink").get("permalink", "")
    save_rows(rows)
    git_push(f"posted {row['date']}")


if __name__ == "__main__":
    main()
