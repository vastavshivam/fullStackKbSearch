# This file contains Pydantic schemas for the application.

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ----------------------------- USER SCHEMAS ----------------------------- #

class UserBase(BaseModel):
    name: str
    email: EmailStr


# class UserCreate(UserBase):
#     password: str


class UserResponse(UserBase):
    id: int
    is_active: bool

    class Config:
        # orm_mode = True
        from_attributes = True


# ----------------------------- ITEM SCHEMAS ----------------------------- #

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    owner_id: int

    class Config:
        # orm_mode = True
        from_attributes = True


# -------------------------- AUTH & TOKEN SCHEMAS ------------------------ #

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


# --------------------------- CHAT MESSAGE SCHEMAS ----------------------- #

class ChatMessage(BaseModel):
    user_id: Optional[int]
    message: str
    sender: str  # 'user' or 'bot'
    timestamp: Optional[datetime] = None
    session_id: str

    class Config:
        # orm_mode = True
        from_attributes = True


# ---------------------------- TICKET SCHEMAS ---------------------------- #

class TicketBase(BaseModel):
    subject: str
    user_id: int
    priority: Optional[str] = "normal"
    status: Optional[str] = "open"
    created_at: Optional[datetime] = None


class TicketCreate(TicketBase):
    description: str


class TicketResponse(TicketBase):
    id: int
    description: str

    class Config:
        # orm_mode = True
        from_attributes = True


# -------------------------- FEEDBACK SCHEMAS ---------------------------- #

class FeedbackCreate(BaseModel):
    ticket_id: int
    rating: int  # 1 to 5
    comment: Optional[str] = None
    sentiment: Optional[str] = None

    class Config:
        # orm_mode = True
        from_attributes = True


# -------------------------- ESCALATION SCHEMAS -------------------------- #

class EscalationCreate(BaseModel):
    ticket_id: int
    reason: str
    escalated_to: str
    timestamp: Optional[datetime] = None

    class Config:
        # orm_mode = True
        from_attributes = True


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    is_active: bool

    class Config:
        # orm_mode = True
        from_attributes = True


class AskRequest(BaseModel):
    question: str
    file_id: str

class AskResponse(BaseModel):
    answer: str


# ----------------------------- KB ENTRY SCHEMAS ----------------------------- #

class KBEntryBase(BaseModel):
    question: str
    answer: str

class KBEntryCreate(KBEntryBase):
    pass

class KBEntryResponse(KBEntryBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class KBEntriesListResponse(BaseModel):
    entries: List[KBEntryResponse]
    total: int

