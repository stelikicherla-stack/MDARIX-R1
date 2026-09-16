import os
import pg8000
from dotenv import load_dotenv

load_dotenv()

conn = pg8000.connect(
    host="localhost",
    port=5433,
    database=os.environ["POSTGRES_DB"],
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
)

try:
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            current_database(),
            current_user,
            current_setting('server_version'),
            EXISTS (
                SELECT 1
                FROM pg_extension
                WHERE extname = 'vector'
            )
    """)

    db, user, version, vector_enabled = cursor.fetchone()

    print("DATABASE =", db)
    print("USER =", user)
    print("POSTGRES =", version)
    print("PGVECTOR =", vector_enabled)

    cursor.execute("SELECT '[1,2,3]'::vector")
    print("VECTOR TEST =", cursor.fetchone()[0])

    print("MDARIX R1 PYTHON DATABASE CONNECTION = PASS")

finally:
    conn.close()
