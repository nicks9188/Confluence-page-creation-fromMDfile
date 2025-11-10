import os
import requests
import markdownify
from urllib.parse import urlparse

# === Hardcoded credentials ===
EMAIL = "<User_Email>"
API_TOKEN = "User_API_Token"
BASE_URL = "<Confluence_Base_URL>"

# === Source URL (space or page) ===
SOURCE_URL = "<Confluence_Page/Space_url/url of the page you want to convert.>"

# === Setup ===
auth = (EMAIL, API_TOKEN)
headers = {"Accept": "application/json"}
os.makedirs("output", exist_ok=True)

# === Determine if it's a space or page ===
def extract_space_key_or_page_id(url):
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if "pages" in parts:
        return "page", parts[-1]
    elif "spaces" in parts:
        idx = parts.index("spaces")
        if idx + 1 < len(parts):
            return "space", parts[idx + 1]
    return None, None

mode, identifier = extract_space_key_or_page_id(SOURCE_URL)

# === Fetch pages ===
pages = []

if mode == "page":
    page_id = identifier
    url = f"{BASE_URL}/rest/api/content/{page_id}?expand=body.storage,children.page"
    res = requests.get(url, auth=auth, headers=headers)
    if res.status_code == 200:
        data = res.json()
        pages.append(data)
        children = data.get("children", {}).get("page", {}).get("results", [])
        pages.extend(children)
    else:
        print("❌ Failed to fetch page:", res.text)

elif mode == "space":
    space_key = identifier
    url = f"{BASE_URL}/rest/api/content?spaceKey={space_key}&limit=100&expand=body.storage"
    res = requests.get(url, auth=auth, headers=headers)
    if res.status_code == 200:
        data = res.json()
        pages = data.get("results", [])
    else:
        print("❌ Failed to fetch space:", res.text)

else:
    print("❌ Invalid URL format.")
    exit()

# === Convert and save ===
for page in pages:
    title = page.get("title", "Untitled").replace("/", "-")
    html = page.get("body", {}).get("storage", {}).get("value", "")
    md = markdownify.markdownify(html, heading_style="ATX")
    with open(f"output/{title}.md", "w", encoding="utf-8") as f:
        f.write(md)


print(f"✅ {len(pages)} pages exported to 'output' folder.")
