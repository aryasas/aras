# gemini-2-5-flash
import os
import requests
import time

# claude-sonnet-4-6
def fetch_geolite():
    # Try api/data first, then data/
    db_path = os.path.join("api", "data", "GeoLite2-Country.mmdb")
    if not os.path.exists(os.path.dirname(db_path)):
        db_path = os.path.join("data", "GeoLite2-Country.mmdb")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Skip if file exists + mtime < 30 days old
    if os.path.exists(db_path):
        mtime = os.path.getmtime(db_path)
        if time.time() - mtime < 30 * 24 * 60 * 60:
            print(f"GeoLite2-Country.mmdb is up to date: {db_path}")
            return

    url = "https://git.io/GeoLite2-Country.mmdb"
    print(f"Downloading GeoLite2-Country.mmdb from {url}...")
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(db_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded to {db_path}")
    except Exception as e:
        print(f"Failed to download GeoLite2-Country.mmdb: {e}")

if __name__ == "__main__":
    fetch_geolite()
