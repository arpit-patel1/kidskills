import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database.database import engine
from app.models.models import Base, Player

def init_db():
    """Initialize the database by creating tables and adding test data."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create a session to add test data
    from sqlalchemy.orm import Session
    with Session(engine) as session:
        # Check if test players already exist
        kid1 = session.query(Player).filter(Player.name == "Kid 1").first()
        kid2 = session.query(Player).filter(Player.name == "Kid 2").first()
        
        # Add test players if they don't exist
        if not kid1:
            kid1 = Player(
                name="Kid 1",
                grade=3,
                preferred_subject="Math",
                preferred_difficulty="Easy"
            )
            session.add(kid1)
            print("Added Kid 1 (Grade 3)")
        
        if not kid2:
            kid2 = Player(
                name="Kid 2",
                grade=2,
                preferred_subject="English",
                preferred_difficulty="Easy"
            )
            session.add(kid2)
            print("Added Kid 2 (Grade 2)")
        
        session.commit()
    
    print("Database initialized successfully!")

if __name__ == "__main__":
    init_db() 