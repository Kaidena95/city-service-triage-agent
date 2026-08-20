from sqlmodel import SQLModel, create_engine, Session

# This is the connection string — tells SQLModel where the database file lives
# "sqlite:///./database.db" means:
#   sqlite    → use SQLite
#   ///       → relative path
#   ./        → current folder (backend/)
#   database.db → the file it creates
DATABASE_URL = "sqlite:///./database.db"

# The engine is the connection between Python and the database file
# connect_args is required for SQLite to work safely with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """
    Creates the database file and all tables if they don't exist yet.
    Called once when the app starts up.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Creates a database session for each request.
    A session is a temporary connection to the database — 
    you use it to read/write data, then it closes automatically.
    FastAPI will call this function automatically via dependency injection.
    """
    with Session(engine) as session:
        yield session
        