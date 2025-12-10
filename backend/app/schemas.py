from datetime import datetime
from pydantic import BaseModel
from typing import Optional


# ===== Клиенты =====

class ClientBase(BaseModel):
    name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    source: Optional[str] = None
    tg_id: Optional[str] = None


class ClientCreate(ClientBase):
    pass


class Client(ClientBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ClientShort(BaseModel):
    id: int
    name: str
    phone: Optional[str] = None
    city: Optional[str] = None

    class Config:
        from_attributes = True


# ===== Тикеты (обращения) =====

class TicketBase(BaseModel):
    client_id: int
    type: str
    last_comment: Optional[str] = None


class TicketCreate(TicketBase):
    pass


class TicketStatusUpdate(BaseModel):
    status: str


class Ticket(BaseModel):
    id: int
    client_id: int
    type: str
    status: str
    last_comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    client: Optional[ClientShort] = None

    class Config:
        from_attributes = True