import os
import pg8000.native
from dotenv import load_dotenv

load_dotenv()

try:
    conn = pg8000.native.Connection(
        host=os.environ["REDSHIFT_HOST"],
        port=int(os.environ["REDSHIFT_PORT"]),
        database=os.environ["REDSHIFT_DB_NAME"],
        user=os.environ["REDSHIFT_USER"],
        password=os.environ["REDSHIFT_PASSWORD"],
    )
    print("connected!")
    result = conn.run("SELECT 1;")
    print(result)
    conn.close()
except Exception as e:
    print("FAILED:", type(e).__name__, "-", e)
