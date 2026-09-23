"""Verify the deployed frontend and check public responses for configured secrets."""
import sys
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urljoin
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from backend.app.config import NVIDIA_API_KEY, SUPABASE_KEY

class Assets(HTMLParser):
    urls = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script" and attrs.get("src"):
            self.urls.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.urls.append(attrs["href"])

base = sys.argv[1].rstrip("/") + "/"
with httpx.Client(timeout=60) as client:
    response = client.get(base)
    assert response.status_code == 200 and '<div id="root">' in response.text
    parser = Assets()
    parser.feed(response.text)
    assert parser.urls
    responses = [response] + [client.get(urljoin(base, url)) for url in parser.urls]
    for response in responses:
        assert response.status_code == 200
        assert all(secret not in response.text for secret in (NVIDIA_API_KEY, SUPABASE_KEY) if secret)
        assert "Traceback (most recent call last)" not in response.text
    for path in (".env", "backend/.env", ".env.local"):
        response = client.get(urljoin(base, path))
        assert response.status_code == 404
        assert all(secret not in response.text for secret in (NVIDIA_API_KEY, SUPABASE_KEY) if secret)
print("PASS: Live HTML/JS/CSS load; configured credentials and stack traces absent; env files inaccessible")
