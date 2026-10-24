import os
import subprocess
import sys

import requests

r = requests.get("https://graph.instagram.com/refresh_access_token", params={
    "grant_type": "ig_refresh_token", "access_token": os.environ["IG_TOKEN"]}, timeout=30)
if not r.ok:
    sys.exit(f"Refresh failed: {r.status_code} {r.text}")
data = r.json()
new_token = data["access_token"]
print("Token refreshed. Expires in", data.get("expires_in"), "seconds.")

if new_token == os.environ["IG_TOKEN"]:
    print("Same token string, nothing to save.")
    sys.exit(0)

# Instagram issued a new string, so the IG_TOKEN secret has to be replaced or posting stops.
# GITHUB_TOKEN can't write secrets, so this needs a GH_PAT secret (see SETUP.md).
if not os.environ.get("GH_TOKEN"):
    sys.exit("Instagram returned a new token but GH_PAT isn't set, so it couldn't be saved. "
             "Generate a new token in the Meta dashboard and update IG_TOKEN by hand.")
print(f"::add-mask::{new_token}")
subprocess.run(["gh", "secret", "set", "IG_TOKEN", "--repo", os.environ["GITHUB_REPOSITORY"]],
               input=new_token, text=True, check=True)
print("Saved the new token to the IG_TOKEN secret.")
