"""
Run once to initialise the database.
Usage: python init_db.py
"""
from database import init_db
from app import seed

print("Initialising database...")
init_db()
print("Seeding default content...")
seed()
print()
print("Done! Default admin login:")
print("  URL:      http://localhost:5000/admin")
print("  Username: admin")
print("  Password: clinton2024")
print()
print("IMPORTANT: Set ADMIN_PASSWORD env variable before deploying to production!")
