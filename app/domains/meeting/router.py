# app\domains\meeting\router.py
# from fastapi import APIRouter, Depends
# from sqlalchemy.orm import Session
# from app.infra.database.session import get_db
# from . import service, schemas

# router = APIRouter(prefix="/meeting", tags=["Meeting"])

# @router.post("/", response_model=schemas.DomainResponse)
# async def create_endpoint(data: schemas.DomainCreate, db: Session = Depends(get_db)):
#     return await service.DomainService.handle_api_request(data, db)