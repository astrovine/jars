from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from application.models.base import get_db
from application.models.waitlist import WaitlistEntry
from sqlalchemy import select

router = APIRouter(tags=["Waitlist"])

class WaitlistCreate(BaseModel):
    email: EmailStr

@router.post("/waitlist", status_code=status.HTTP_201_CREATED)
async def join_waitlist(data: WaitlistCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(WaitlistEntry).filter(WaitlistEntry.email == data.email))
    if result.scalar_one_or_none():
        return {"message": "Email already on waitlist"}
    
    entry = WaitlistEntry(email=data.email)
    db.add(entry)
    await db.commit()
    return {"message": "Joined waitlist successfully"}
