# src/db/database.py
import os # used to read environment variables
from dotenv import load_dotenv # loads variables from a .env file
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# orm is the Object Relational Mapper for Python and SQLAlchemy is an Object Relational Mapping (ORM) library for Python. To interact with databases in Python, you can use an ORM to manage data via Python classes and objects rather than writing SQL.

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL) # Creates the connection interface between your application and the database.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) # A session is basically the object your application uses to communicate with the database for a particular unit of work.
#A session is what your application uses to perform database operations.
# bind = engine means This connects the session factory to your previously created engine
# autocommit=False means that changes made in the session are not automatically committed to the database. You have to explicitly call commit() to save changes.
# autoflush=False means that changes made in the session are not automatically flushed to the database. You have to explicitly call flush() to save changes.
Base = declarative_base()  #Creates the base class from which your database models inherit.


def get_db():
    """Gives each request its own database session, closes it when done."""
    db = SessionLocal() # creates an actual database session
    try:
        yield db # returns the database session, This is commonly used with FastAPI dependencies.
    finally:
        db.close()

# "Here is the database session. Use it while the request is running. When you're finished, I'll continue and close it.