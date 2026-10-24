"""Add a post to posts.csv.

  python3 add_post.py                       # asks for each field
  python3 add_post.py --date 2026-11-02 --headline "..." --subline "..." --caption-file caption.txt
  python3 add_post.py ... --image "posts/a.jpg|posts/b.jpg"   # your own images (carousel)
"""
import argparse
from datetime import date, timedelta

from post import load_rows, save_rows, validate

EVERY_N_DAYS = 2


def next_free_date(rows):
    taken = {r["date"] for r in rows}
    d = max([date.fromisoformat(r["date"]) for r in rows] + [date.today()]) + timedelta(days=EVERY_N_DAYS)
    while d.isoformat() in taken:
        d += timedelta(days=1)
    return d.isoformat()


def ask(label, default=""):
    v = input(f"{label}{f' [{default}]' if default else ''}: ").strip()
    return v or default


def ask_multiline(label):
    print(f"{label} (finish with a line containing only a dot):")
    lines = []
    while (line := input()) != ".":
        lines.append(line)
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--date")
    p.add_argument("--headline")
    p.add_argument("--subline", default=None)
    p.add_argument("--caption")
    p.add_argument("--caption-file")
    p.add_argument("--image", default=None)
    a = p.parse_args()

    rows = load_rows()
    caption = a.caption or (open(a.caption_file, encoding="utf-8").read().strip() if a.caption_file else None)
    row = {
        "date": a.date or (next_free_date(rows) if a.headline else ask("Date (YYYY-MM-DD)", next_free_date(rows))),
        "headline": a.headline or ask("Headline (big text on the image)"),
        "subline": a.subline if a.subline is not None else ask("Subline (small text, optional)"),
        "caption": caption or ask_multiline("Caption"),
        "image": a.image if a.image is not None else ask("Your own image path(s), | separated (blank = auto thumbnail)"),
        "posted": "no",
        "media_id": "",
        "permalink": "",
    }
    date.fromisoformat(row["date"])
    validate(row)
    if any(r["date"] == row["date"] for r in rows):
        print(f"Note: another post is already scheduled on {row['date']}; they'll go out on consecutive runs.")

    rows.append(row)
    rows.sort(key=lambda r: r["date"])
    save_rows(rows)
    print(f"Added post for {row['date']}. Run python3 preview.py to see it.")


if __name__ == "__main__":
    main()
