
import asyncio
import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

async def check_schema():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    # Using synchronous engine for inspection as it's easier for quick check
    if db_url.startswith("postgresql+asyncpg"):
        db_url = db_url.replace("postgresql+asyncpg", "postgresql")
    
    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
        columns = inspector.get_columns('models')
        
        print("\nColumns in 'models' table:")
        column_names = [c['name'] for c in columns]
        for name in column_names:
            print(f"- {name}")
            
        required = ['model_name', 'model_description', 'model_provider', 'model_type', 'tool_support', 'model_image', 'context_window', 'id', 'created_at', 'updated_at', 'is_active']
        missing = [r for r in required if r not in column_names]
        
        if missing:
            print(f"\nCRITICAL: Missing columns: {missing}")
        else:
            print("\nAll required columns are present.")
            
    except Exception as e:
        print(f"Error checking schema: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
