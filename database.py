from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Get the database connection details from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")
ENV = os.getenv("ENV")

# Create the database URL
if(ENV == "prod"):
    SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
elif(ENV == "dev"):
    SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/sehatyuk"


# Create the engine using the database URL
engine = create_engine(
    SQLALCHEMY_DATABASE_URL
)

# Configure the session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declare the base class for the ORM models
BaseDB = declarative_base()