import time
from app.config import settings
from app.db.models import Base
from app.db.seed import seed_sales_data
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

try:
  engine = create_engine(settings.database_url, pool_pre_ping=True)
  SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
  readonly_engine = create_engine(
      settings.readonly_database_url, pool_pre_ping=True
  )
except Exception:
  engine = None
  SessionLocal = None
  readonly_engine = None


def init_db():
  connected = False
  for _ in range(10):
    try:
      with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
      connected = True
      break
    except Exception:
      time.sleep(2)

  if not connected:
    raise RuntimeError("could not connect to database after retries")

  Base.metadata.create_all(bind=engine)

  with engine.connect() as conn:
    # hnsw index speeds up cosine similarity searches
    conn.execute(
        text(
            "CREATE INDEX IF NOT EXISTS chunk_vector_idx ON document_chunks"
            " USING hnsw (embedding vector_cosine_ops);"
        )
    )
    conn.execute(
        text("""
      DO $$
      BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_user') THEN
          CREATE USER readonly_user WITH PASSWORD 'readonly_pass';
        END IF;
      END
      $$;
      GRANT CONNECT ON DATABASE docpilot TO readonly_user;
      GRANT USAGE ON SCHEMA public TO readonly_user;
      GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
      ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO readonly_user;
    """)
    )
    conn.commit()

  with SessionLocal() as db:
    seed_sales_data(db)


def get_db():
  if SessionLocal is None:
    raise RuntimeError("database engine is not configured")
  db = SessionLocal()
  try:
    yield db
  finally:
    db.close()
