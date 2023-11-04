from fastapi import FastAPI, HTTPException, Depends
from typing import Annotated, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel
from database import SessionLocal, engine
import models
from models import Base
from fastapi.middleware.cors import CORSMiddleware

Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    games_played: int
    high_score: int
    current_score: int

    class Config:
        orm_mode = True

class UserScoreResponse(BaseModel):
    id: int
    username: str
    games_played: int
    high_score: int
    current_score: int
    game_won: bool

    class Config:
        orm_mode = True

class ScoreUpdate(BaseModel):
    correct: bool

class UserHighScore(BaseModel):
    username: str
    high_score: int

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    new_user = models.User(username=user.username, games_played=0, high_score=0, current_score=0)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/login/", response_model=User)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Username not found")
    return db_user

@app.get("/users/by_username/{username}", response_model=User)
def read_user_by_username(username: str, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/users/{user_id}", response_model=User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@app.get("/highscores", response_model=List[UserHighScore])
def get_high_scores(db: Session = Depends(get_db)):
    users = db.query(models.User).order_by(desc(models.User.high_score)).all()
    return [{"username": user.username, "high_score": user.high_score} for user in users]

@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: User, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.games_played = user.games_played
    db_user.high_score = user.high_score
    db.commit()
    db.refresh(db_user)
    return db_user

@app.put("/users/{user_id}/update_score", response_model=UserScoreResponse)
def update_score(user_id: int, score_update: ScoreUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    game_won = False  # Flag to indicate if the user has won the game
    previous_current_score = db_user.current_score

    if score_update.correct:
        db_user.current_score += 1
        if db_user.current_score >= 10:  # Winning condition
            game_won = True
            db_user.high_score = max(db_user.high_score, db_user.current_score)
            
    else:
        db_user.high_score = max(db_user.high_score, db_user.current_score)

    db_user.games_played += 1 
    
    db.commit()
    db.refresh(db_user)

    response = UserScoreResponse(
        id=db_user.id,
        username=db_user.username,
        games_played=db_user.games_played,
        high_score=db_user.high_score,
        current_score=db_user.current_score,
        game_won=game_won
    )

    if game_won or not score_update.correct:
        db_user.current_score = 0
        db.commit()
        db.refresh(db_user)

    return response