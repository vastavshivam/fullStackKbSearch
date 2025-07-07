from sqlalchemy.orm import Session
from models.db_models import ChatLog, Ticket, UserFeedback, HumanEscalation
from models.schemas import ChatMessage, TicketCreate, FeedbackCreate, EscalationCreate
from sqlalchemy.future import select
from database.database import async_session
from models.db_models import User
from sqlalchemy.ext.asyncio import AsyncSession
# 💬 Save Chat Message
from datetime import datetime

async  def save_chat_message(db: AsyncSession, msg: ChatMessage):
    timestamp = msg.timestamp
    if timestamp.tzinfo is not None:
        timestamp = timestamp.replace(tzinfo=None)
    # print (f" db data {db}") 
    chat = ChatLog(session_id=msg.session_id,
        user_input=msg.message,
        bot_response=msg.sender,
        timestamp=timestamp)
    db.add(chat)
    await db.commit()         # ✅ await required for async session
    await db.refresh(chat)    # ✅ await required
    return chat

# 📩 Get All Chat Logs for a User
def get_user_chats(db: Session, user_id: int):
    return db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp).all()

# 💬 Get Conversation History (multi-turn)
def get_conversation_context(db: Session, user_id: int, limit: int = 10):
    return db.query(ChatLog).filter(ChatLog.user_id == user_id).order_by(ChatLog.timestamp.desc()).limit(limit).all()[::-1]

# 🎟️ Create Support Ticket
def create_ticket(db: Session, ticket: TicketCreate):
    new_ticket = Ticket(**ticket.dict())
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    return new_ticket

# 🎟️ Get Ticket by ID
def get_ticket(db: Session, ticket_id: int):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()

# 🎟️ Update Ticket Status
def update_ticket_status(db: Session, ticket_id: int, status: str):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket:
        ticket.status = status
        db.commit()
        db.refresh(ticket)
    return ticket

# 🎟️ Delete Ticket
def delete_ticket(db: Session, ticket_id: int):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket:
        db.delete(ticket)
        db.commit()
    return ticket

# 👍👎 Save Feedback
def save_feedback(db: Session, feedback: FeedbackCreate):
    fb = UserFeedback(**feedback.dict())
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return fb

# 📊 Get Feedback by Chat ID
def get_feedback_for_chat(db: Session, chat_id: int):
    return db.query(UserFeedback).filter(UserFeedback.chat_id == chat_id).all()

#  Save Human Escalation Record
def escalate_to_human(db: Session, escalation: EscalationCreate):
    es = HumanEscalation(**escalation.dict())
    db.add(es)
    db.commit()
    db.refresh(es)
    return es

# 📥 Get All Escalations
def get_escalation_queue(db: Session):
    return db.query(HumanEscalation).order_by(HumanEscalation.timestamp.desc()).all()

# async def get_user_by_email(email: str):
#     async with async_session() as session:
#         result = await session.execute(select(User).where(User.email == email))
#         user = result.scalar_one_or_none()
#         return user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user, hashed_password: str):
    db_user = User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user
    


