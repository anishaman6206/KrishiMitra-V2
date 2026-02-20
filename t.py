from sqlalchemy import create_engine, inspect
import os
engine = create_engine(os.environ.get("KM_DATABASE_URL","sqlite:///backend/local.db"))
insp = inspect(engine)
print("Tables:", insp.get_table_names())