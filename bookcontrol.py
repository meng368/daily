from fastapi import FastAPI, HTTPException,Depends,Form,File,UploadFile,Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session
from pydantic import BaseModel
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
app = FastAPI()
limiter = Limiter(key_func = get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
BASEURL =  "sqlite:///./test.db"
engine = create_engine(BASEURL, connect_args={"check_same_thread": False})
BASE = declarative_base()
class Data(BASE):
    __tablename__ = 'user'
    id =Column(Integer,primary_key=True,index=True)
    name=Column(String,nullable=False,unique=True)
    picture= Column(String)
    introduce =Column(String)
BASE.metadata.create_all(bind=engine)
SessionLocal= sessionmaker(bind=engine,autoflush=False,autocommit=False)
class Book(BaseModel):
    name:str
    picture:str
    introduce:str
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@app.get('/booklist')
@limiter.limit('50/minute')
def get_book(request:Request,db:Session=Depends(get_db)):
    data = db.query(Data).all()
    return data
@app.post('/createbook')
@limiter.limit('10/minute')
def create_book(request:Request,name:str = Form(),introduce:str = Form(),picture:UploadFile = File(),db:Session=Depends(get_db)):
    existing = db.query(Data).filter(Data.name==name).first()
    if existing:
        raise HTTPException(status_code=400,detail='该书已经登录在案')
    import os
    upload_dir = 'static/uploads'
    os.makedirs(upload_dir,exist_ok=True)
    file_path = os.path.join(upload_dir,picture.filename)
    with open(file_path,'wb') as f:
        f.write(picture.file.read())
    new_book = Data(
        name = name,
        picture =file_path,
        introduce = introduce,
    )
    db.add(new_book)
    db.commit()
    db.refresh(new_book)
    return {'message':'添加图书成功'}
    

