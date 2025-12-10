from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship

from .db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(String, unique=True, index=True)      # telegram user id (строкой)
    username = Column(String, nullable=True)
    role = Column(String, default="manager")             # manager / admin

    tickets = relationship("Ticket", back_populates="assignee")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    tg_id = Column(String, nullable=True, index=True)    # если клиент из тг
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    city = Column(String, nullable=True)
    source = Column(String, nullable=True)               # откуда пришёл: qr, реклама...

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    tickets = relationship("Ticket", back_populates="client")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"))
    type = Column(String, nullable=False)                # заказ / вопрос / гарантия / работа и тд
    status = Column(String, default="new")               # new / in_progress / waiting / closed
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_comment = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    client = relationship("Client", back_populates="tickets")
    assignee = relationship("User", back_populates="tickets")
