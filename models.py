from sqlalchemy import Column, Integer, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)

class Activity(Base):
    __tablename__ = 'activity'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    action_type = Column(String)
    target_url = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

engine = create_engine("sqlite:///botdata.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
