"""Render every unposted post into preview/ and open a page showing them like Instagram.

  python3 preview.py
"""
import html
import shutil
import subprocess
import sys
from pathlib import Path

from make_thumb import make_thumb
from post import image_files, load_rows

OUT = Path("preview")


def main():
    rows = [r for r in load_rows() if r["posted"].strip().lower() != "yes"]
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()

    cards, problems = [], []
    for r in rows:
        files = image_files(r)
        if files:
            missing = [f for f in files if not Path(f).exists()]
            if missing:
                problems.append(f"{r['date']}: missing {missing}")
            imgs = [f"../{f}" for f in files if Path(f).exists()]
        else:
            out = OUT / f"{r['date']}.jpg"
            make_thumb(r["headline"], r["subline"], str(out))
            imgs = [out.name]

        caption = r["caption"]
        if len(caption) > 2200:
            problems.append(f"{r['date']}: caption too long ({len(caption)} chars)")
        if caption.count("#") > 30:
            problems.append(f"{r['date']}: too many hashtags")

        img_tags = "".join(f'<img src="{html.escape(i)}">' for i in imgs)
        cards.append(f"""
<article>
  <header>{html.escape(r['date'])}{' · carousel of ' + str(len(imgs)) if len(imgs) > 1 else ''}</header>
  <div class="imgs">{img_tags}</div>
  <p>{html.escape(caption).replace(chr(10), '<br>')}</p>
  <footer>{len(caption)}/2200 chars · {caption.count('#')} hashtags</footer>
</article>""")

    page = f"""<!doctype html><meta charset="utf-8"><title>Upcoming posts</title>
<style>
body{{font:15px -apple-system,Helvetica,sans-serif;background:#fafafa;margin:0;padding:24px;color:#111}}
h1{{font-size:20px}} .bad{{background:#fee;border:1px solid #f99;padding:12px;border-radius:8px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:24px}}
article{{background:#fff;border:1px solid #ddd;border-radius:10px;overflow:hidden}}
header,footer{{padding:10px 14px;font-weight:600}} footer{{font-weight:400;color:#888;font-size:13px}}
.imgs{{display:flex;overflow-x:auto;scroll-snap-type:x mandatory}}
.imgs img{{width:100%;flex:none;scroll-snap-align:start;aspect-ratio:4/5;object-fit:cover}}
p{{padding:0 14px;line-height:1.4}}
</style>
<h1>{len(rows)} upcoming post(s)</h1>
{''.join(f'<p class="bad">{html.escape(p)}</p>' for p in problems)}
<main>{''.join(cards)}</main>"""
    (OUT / "index.html").write_text(page, encoding="utf-8")
    print(f"Wrote {OUT / 'index.html'}")
    for p in problems:
        print("PROBLEM:", p)
    if sys.platform == "darwin" and "--no-open" not in sys.argv:
        subprocess.run(["open", str(OUT / "index.html")])


if __name__ == "__main__":
    main()
