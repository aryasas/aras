import os
import sys
import time
import mariadb

print("Waiting for MariaDB...")
host = os.getenv("DB_HOST")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")
port_env = os.getenv("DB_PORT")
print(f"Connecting to {host}:{port_env} as {user} for database {database}")
port = int(port_env) if port_env else 3306

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
