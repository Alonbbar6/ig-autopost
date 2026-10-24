# IG autopost setup (official Instagram API)

## 1. Meta developer app (about 15 min)
1. Go to developers.facebook.com, log in, click My Apps > Create App.
2. Use case: "Manage messaging & content on Instagram". Name it "Bardales Labs Autopost".
3. In the app, open Instagram > API setup with Instagram login.
4. Under "Generate access tokens", click Add account and log in as @bardaleslabs.
   The account must be a Business or Creator account (Instagram app > Settings > Account type).
5. Click Generate token. Copy the token and the Instagram user ID shown next to it.
   This is a long-lived token (about 60 days). The workflow refreshes it on the 1st and 15th.
6. You do NOT need App Review to post to your own account while the app is in development mode.

## 2. GitHub repo
1. Create a new PUBLIC repo called ig-autopost (public so Instagram can fetch the images).
2. Upload everything in this folder, including the hidden .github folder.
3. Repo > Settings > Secrets and variables > Actions > New repository secret:
   - IG_USER_ID = the user ID from step 1.5
   - IG_TOKEN = the token from step 1.5
   - GH_PAT = a fine-grained GitHub token (github.com/settings/personal-access-tokens) with access
     to only this repo and "Secrets: Read and write". If Instagram hands back a new token string
     when refreshing, this lets the workflow save it. Without it, the refresh job fails with a
     message telling you to paste a new token by hand.
4. Repo > Settings > Actions > General > Workflow permissions > Read and write.

## 3. Test
Actions tab > Instagram autopost > Run workflow, tick "Dry run" first. It makes the thumbnail and
prints the image URL without posting. Then run it again without dry run to really post.

## Daily use (on your Mac, in this folder)
- Add a post:            python3 add_post.py
  It asks for headline, subline and caption, and picks the next free date (every 2 days).
  Or in one line: python3 add_post.py --headline "..." --subline "..." --caption-file caption.txt
- Preview what's coming:  python3 preview.py
  Opens a page showing every unposted image and caption, and flags problems
  (caption over 2200 chars, more than 30 hashtags, missing image files).
- Push to GitHub (git add -A && git commit -m "new posts" && git push), or edit posts.csv on GitHub.

posts.csv columns: date, headline, subline, caption, image, posted, media_id.
- Leave image blank to auto-generate a branded thumbnail from the headline and subline.
- Or put your own JPEGs in posts/ and write the path in the image column.
- For a carousel (up to 10 images), separate paths with |, e.g. posts/a.jpg|posts/b.jpg
- One post per run, oldest due first. Dates are Miami time.

It posts at 16:17 UTC: 12:17pm Miami in summer, 11:17am in winter.
If a run publishes but fails to save, the next run sees the caption is already on Instagram and
just marks the row as posted instead of posting twice.

## Managing from the portfolio admin
Your portfolio has a private page at /admin (password login) that edits this repo for you:
add, edit, delete and reorder carousel images, preview posts like Instagram, start a run
("Post next due now" or "Dry run") and see recent runs. Each save is one commit to posts.csv
(plus any uploaded JPEGs in posts/), so the CLI scripts above keep working side by side.
After editing on the website, run git pull here before using add_post.py.
