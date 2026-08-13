from dotenv import load_dotenv
import os

load_dotenv()

print("🔍 Testing PostgreSQL Setup...")
print("-" * 50)

# Check environment
db_url = os.getenv('DATABASE_URL')
if db_url:
    print("✅ DATABASE_URL found in .env")
else:
    print("❌ DATABASE_URL not found!")

# Test database connection
from etl.database import test_connection, init_db
if test_connection():
    init_db()
    print("\n🎉 Everything is working! Ready to build the project.")
