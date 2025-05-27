# init_db.py
from database import Base, engine
import models  # Ensures Email and User models are loaded

def init():
    print("📦 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Done.")

if __name__ == "__main__":
    init()
