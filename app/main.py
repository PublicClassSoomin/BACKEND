# app\main.py
"""
Railway 배포 환경에서도 PyMySQL을 MySQLdb 호환 드라이버로 사용할 수 있게 설정합니다.
"""
import pymysql
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
<<<<<<< HEAD
# 각 도메인에서 router 만들어서 연결해주세요.
=======

>>>>>>> main
from app.api.v1.api_router import api_router
from app.core.lifespan import lifespan

pymysql.install_as_MySQLdb()

app = FastAPI(
    title="Meeting Assistant Agent API",
    lifespan=lifespan,
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    # Vite dev servers
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Meeting Assistant Agent API is running!"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


app.include_router(api_router, prefix="/api/v1")
