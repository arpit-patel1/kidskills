import os
import sys

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import Column, String
from app.database.database import engine
from app.models.models import Base, Player, Progress

def migrate_add_sub_activity():
    """
    Migration script to add sub_activity columns to existing tables.
    This handles adding the columns and setting default values.
    """
    from sqlalchemy import text
    from sqlalchemy.orm import Session
    
    print("Starting migration to add sub-activity columns...")
    
    with Session(engine) as session:
        # Check if the columns already exist
        try:
            # First check if the column already exists in the players table
            session.execute(text("SELECT preferred_sub_activity FROM players LIMIT 1"))
            players_column_exists = True
        except Exception:
            players_column_exists = False
            
        try:
            # Check if the column already exists in the progress table
            session.execute(text("SELECT sub_activity FROM progress LIMIT 1"))
            progress_column_exists = True
        except Exception:
            progress_column_exists = False
        
        # Add columns if they don't exist
        if not players_column_exists:
            print("Adding preferred_sub_activity column to players table...")
            session.execute(text("ALTER TABLE players ADD COLUMN preferred_sub_activity VARCHAR DEFAULT 'Addition/Subtraction'"))
        else:
            print("preferred_sub_activity column already exists in players table.")
            
        if not progress_column_exists:
            print("Adding sub_activity column to progress table...")
            session.execute(text("ALTER TABLE progress ADD COLUMN sub_activity VARCHAR"))
        else:
            print("sub_activity column already exists in progress table.")
        
        # Set default values based on subject for all existing players
        players = session.query(Player).all()
        for player in players:
            if player.preferred_sub_activity is None:
                if player.preferred_subject == "Math":
                    player.preferred_sub_activity = "Addition/Subtraction"
                else:  # English
                    player.preferred_sub_activity = "Opposites/Antonyms"
                print(f"Set default sub-activity for {player.name} to {player.preferred_sub_activity}")
        
        session.commit()
        
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_add_sub_activity() 