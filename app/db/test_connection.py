from sqlalchemy import text
from app.db.database import engine

with engine.connect() as conn:
    result = conn.execute(text("SELECT version();"))
    print(result.scalar())
