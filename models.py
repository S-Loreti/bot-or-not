from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    games_played = Column(Integer, default=0)
    high_score = Column(Integer, default=0)
    current_score = Column(Integer, default=0)
    game_won = Column(Boolean, default=False)