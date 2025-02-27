
from sqlalchemy import create_engine, Column, String, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import DateTime


Base = declarative_base()
DATABASE_URL = "sqlite:///users.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    blocked = Column(Boolean, default=False)
    last_order_time = Column(DateTime, nullable=True)  


async def save_or_update_user(user_id, username=None, phone=None):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user:
            if username:
                user.username = username
            if phone:
                user.phone = phone
        else:
            user = User(user_id=user_id, username=username, phone=phone)
            session.add(user)
        session.commit()
    finally:
        session.close()

def get_user(user_id):
    session = SessionLocal()
    try:
        return session.query(User).filter(User.user_id == user_id).first()
    finally:
        session.close()


Base.metadata.create_all(bind=engine)