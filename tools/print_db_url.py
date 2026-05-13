import sys
import os
sys.path.append(os.path.join(os.getcwd(), 'api'))
from core.lib.database import DATABASE_URL
print(f"DATABASE_URL: {DATABASE_URL}")
