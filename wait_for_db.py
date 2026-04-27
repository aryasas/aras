import os
import sys
import time
import mariadb

print("Waiting for MariaDB...")
host = os.getenv("DB_HOST", "db")
user = os.getenv("DB_USER", "aras")
password = os.getenv("DB_PASSWORD", "araspass")
database = os.getenv("DB_NAME", "arasdb")
port = int(os.getenv("DB_PORT", 3306))

for i in range(20): # Try to connect 20 times with 3-second intervals
    try:
        conn = mariadb.connect(
            host=host,
            user=user,
            password=password,
            database=database,
            port=port
        )
        conn.close()
        print("MariaDB is ready!")
        break
    except mariadb.Error as e:
        print(f"MariaDB not ready yet: {e}")
        time.sleep(3)
else:
    print("MariaDB did not become ready in time. Exiting.")
    sys.exit(1)
