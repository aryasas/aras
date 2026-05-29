# gemini-2-5-flash
import maxminddb
import os
import logging
from typing import Optional

_reader: Optional[maxminddb.Reader] = None
_warned_missing = False

def country_from_ip(ip: str) -> Optional[str]:
    global _reader, _warned_missing
    if _reader is None:
        # Search for GeoLite2-Country.mmdb in common locations
        possible_paths = [
            os.path.join("api", "data", "GeoLite2-Country.mmdb"),
            os.path.join("data", "GeoLite2-Country.mmdb"),
            "/usr/share/GeoIP/GeoLite2-Country.mmdb"
        ]
        db_path = None
        for path in possible_paths:
            if os.path.exists(path):
                db_path = path
                break
                
        if not db_path:
            if not _warned_missing:
                logging.warning("GeoLite2-Country.mmdb not found. Geo-routing will be disabled. Run 'python manage.py fetch-geo' to enable.")
                _warned_missing = True
            return None
            
        try:
            _reader = maxminddb.open_database(db_path)
        except Exception as e:
            logging.error(f"Failed to open GeoLite2 database: {e}")
            return None

    try:
        response = _reader.get(ip)
        if response and "country" in response:
            return response["country"]["iso_code"]
    except Exception as e:
        logging.error(f"Geo IP lookup failed for {ip}: {e}")
        
    return None
