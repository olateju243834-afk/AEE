import os
import psycopg2

# Render provides your DATABASE_URL in environment variables
DATABASE_URL = os.environ['DATABASE_URL']

conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# List all tables in the current schema
cur.execute("""
    SELECT table_schema, table_name
    FROM information_schema.tables
    WHERE table_type='BASE TABLE' AND table_schema='public';
""")

tables = cur.fetchall()
print("Tables in database:")
for schema, name in tables:
    print(f"{schema}.{name}")

cur.close()
conn.close()
