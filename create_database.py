"""
Create the transactions_db database
"""
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Connect to PostgreSQL server (default postgres database)
conn = psycopg2.connect(
    dbname='postgres',
    user='postgres',
    password='Vish@1724',
    host='localhost',
    port='5432'
)

# Set connection to autocommit mode
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

# Create database
cursor = conn.cursor()

# Check if database exists
cursor.execute("SELECT 1 FROM pg_database WHERE datname='transactions_db'")
exists = cursor.fetchone()

if not exists:
    cursor.execute('CREATE DATABASE transactions_db')
    print("✓ Database 'transactions_db' created successfully!")
else:
    print("✓ Database 'transactions_db' already exists")

cursor.close()
conn.close()

print("\nNow run: python -c \"from app.database.base import init_db; init_db()\"")
