from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional

from . import models, schemas
from .db import engine, Base
from .deps import get_db

# Создаём таблицы (на старте)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="JMih CRM API",
    version="0.3.0",
)


@app.get("/ping")
def ping():
    return {"status": "ok"}


# ===== Клиенты =====

@app.post("/clients", response_model=schemas.Client)
def create_client(client_in: schemas.ClientCreate, db: Session = Depends(get_db)):
    client = models.Client(**client_in.dict())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@app.get("/clients", response_model=List[schemas.Client])
def list_clients(db: Session = Depends(get_db)):
    clients = db.query(models.Client).order_by(models.Client.id.desc()).all()
    return clients


# ===== Тикеты (обращения) =====

@app.post("/tickets", response_model=schemas.Ticket)
def create_ticket(ticket_in: schemas.TicketCreate, db: Session = Depends(get_db)):
    # проверяем, что клиент существует
    client = db.query(models.Client).filter(models.Client.id == ticket_in.client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    ticket = models.Ticket(
        client_id=ticket_in.client_id,
        type=ticket_in.type,
        last_comment=ticket_in.last_comment,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=List[schemas.Ticket])
def list_tickets(
    status: Optional[str] = Query(None),
    client_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Ticket)
        .options(joinedload(models.Ticket.client))
        .order_by(models.Ticket.created_at.desc())
    )

    if status:
        q = q.filter(models.Ticket.status == status)
    if client_id:
        q = q.filter(models.Ticket.client_id == client_id)

    return q.all()


@app.patch("/tickets/{ticket_id}/status", response_model=schemas.Ticket)
def change_ticket_status(
    ticket_id: int,
    status_in: schemas.TicketStatusUpdate,
    db: Session = Depends(get_db),
):
    ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = status_in.status
    db.commit()
    db.refresh(ticket)
    return ticket


# ===== Мини-приложение (webapp) =====

@app.get("/webapp", response_class=HTMLResponse)
def webapp():
    # Простой HTML + JS, который работает и в браузере, и в Telegram WebApp
    return """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <title>JMih CRM</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <style>
        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            margin: 0;
            padding: 16px;
            background: #0b0f10;
            color: #f5f5f5;
        }
        h1 {
            font-size: 20px;
            margin-bottom: 12px;
        }
        .subtitle {
            font-size: 13px;
            color: #9ca3af;
            margin-bottom: 16px;
        }
        .container {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        .card {
            border-radius: 12px;
            padding: 12px 14px;
            background: #111827;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        }
        .card h2 {
            font-size: 16px;
            margin: 0 0 8px;
        }
        label {
            display: block;
            font-size: 13px;
            margin-bottom: 4px;
        }
        input, select {
            width: 100%;
            box-sizing: border-box;
            padding: 8px 10px;
            border-radius: 8px;
            border: 1px solid #374151;
            background: #020617;
            color: #f9fafb;
            font-size: 14px;
            margin-bottom: 8px;
        }
        input::placeholder {
            color: #6b7280;
        }
        button {
            width: 100%;
            padding: 10px 12px;
            border-radius: 10px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            background: #22c55e;
            color: #022c22;
        }
        button:disabled {
            opacity: 0.6;
            cursor: default;
        }
        .clients-list,
        .tickets-list {
            max-height: 260px;
            overflow-y: auto;
        }
        .client-item,
        .ticket-item {
            padding: 8px 8px;
            border-radius: 8px;
            background: #020617;
            border: 1px solid #111827;
            margin-bottom: 6px;
            font-size: 13px;
        }
        .client-item .name,
        .ticket-item .title {
            font-weight: 600;
        }
        .client-item .meta,
        .ticket-item .meta {
            color: #9ca3af;
            font-size: 12px;
            margin-top: 2px;
        }
        .status-bar {
            font-size: 12px;
            color: #9ca3af;
            margin-top: 4px;
        }
        .ticket-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .badge {
            padding: 2px 8px;
            border-radius: 999px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        .badge-new {
            background: rgba(34, 197, 94, 0.16);
            color: #4ade80;
        }
        .badge-in_progress {
            background: rgba(59, 130, 246, 0.16);
            color: #60a5fa;
        }
        .badge-waiting {
            background: rgba(245, 158, 11, 0.16);
            color: #fbbf24;
        }
        .badge-closed {
            background: rgba(148, 163, 184, 0.16);
            color: #e5e7eb;
        }
        .ticket-actions {
            margin-top: 6px;
            display: flex;
            gap: 6px;
        }
        .ticket-actions button {
            width: auto;
            padding: 6px 10px;
            font-size: 12px;
        }
        .btn-secondary {
            background: #1f2937;
            color: #e5e7eb;
        }
        .filter-row {
            margin: 6px 0 10px;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }
        .filter-btn {
            padding: 6px 10px;
            border-radius: 999px;
            border: none;
            font-size: 11px;
            cursor: pointer;
            background: #020617;
            color: #e5e7eb;
        }
        .filter-btn.active {
            background: #22c55e;
            color: #022c22;
        }
    </style>
</head>
<body>
    <h1>JMih mini-CRM</h1>
    <div class="subtitle">
        Мини-панель для работы с клиентами ЖМЫХ. Добавляй клиентов и накидывай базу, а ниже — тикеты.
    </div>
    <div class="container">
        <div class="card">
            <h2>Новый клиент</h2>
            <form id="clientForm">
                <label>Имя</label>
                <input type="text" id="name" placeholder="Иван / Ник ЖМЫХ" required />

                <label>Телефон</label>
                <input type="tel" id="phone" placeholder="79990000000" />

                <label>Город / филиал</label>
                <input type="text" id="city" placeholder="СПБ / Норильск / Красноярск" />

                <label>Источник</label>
                <input type="text" id="source" placeholder="QR, реклама, бот, живая точка..." />

                <button type="submit" id="submitBtn">Сохранить клиента</button>
                <div class="status-bar" id="status"></div>
            </form>
        </div>

        <div class="card">
            <h2>Клиенты</h2>
            <div class="clients-list" id="clientsList">
                Загрузка...
            </div>
        </div>

        <div class="card">
            <h2>Новое обращение</h2>
            <form id="ticketForm">
                <label>Клиент</label>
                <select id="ticketClient" required>
                    <option value="">Выбери клиента...</option>
                </select>

                <label>Тип</label>
                <select id="ticketType">
                    <option value="order">Заказ</option>
                    <option value="question">Вопрос</option>
                    <option value="warranty">Гарантия</option>
                    <option value="job">Работа</option>
                    <option value="other">Другое</option>
                </select>

                <label>Комментарий</label>
                <input type="text" id="ticketComment" placeholder="Что хочет клиент / детали" />

                <button type="submit" id="ticketSubmitBtn">Создать обращение</button>
                <div class="status-bar" id="ticketStatus"></div>
            </form>
        </div>

        <div class="card">
            <h2>Обращения</h2>
            <div class="filter-row" id="ticketFilters">
                <button class="filter-btn active" data-status="">Все</button>
                <button class="filter-btn" data-status="new">Новые</button>
                <button class="filter-btn" data-status="in_progress">В работе</button>
                <button class="filter-btn" data-status="waiting">Ждём клиента</button>
                <button class="filter-btn" data-status="closed">Закрытые</button>
            </div>
            <div class="tickets-list" id="ticketsList">
                Загрузка...
            </div>
        </div>
    </div>

    <!-- Telegram WebApp SDK (на будущее) -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script>
        const apiBase = window.location.origin;

        const clientsListEl = document.getElementById("clientsList");
        const form = document.getElementById("clientForm");
        const statusEl = document.getElementById("status");
        const submitBtn = document.getElementById("submitBtn");

        const ticketsListEl = document.getElementById("ticketsList");
        const ticketForm = document.getElementById("ticketForm");
        const ticketStatusEl = document.getElementById("ticketStatus");
        const ticketClientSelect = document.getElementById("ticketClient");
        const ticketTypeInput = document.getElementById("ticketType");
        const ticketCommentInput = document.getElementById("ticketComment");
        const ticketSubmitBtn = document.getElementById("ticketSubmitBtn");
        const ticketFiltersEl = document.getElementById("ticketFilters");

        let clientsCache = [];
        let currentStatusFilter = "";

        // Если открыто в Telegram WebApp — чуть расширяем окно
        try {
            if (window.Telegram && window.Telegram.WebApp) {
                window.Telegram.WebApp.ready();
                window.Telegram.WebApp.expand();
            }
        } catch (e) {
            console.log("Telegram WebApp init error:", e);
        }

        async function fetchClients() {
            clientsListEl.innerHTML = "Загрузка...";
            try {
                const res = await fetch(apiBase + "/clients");
                if (!res.ok) {
                    throw new Error("Ошибка загрузки");
                }
                const data = await res.json();
                clientsCache = data;
                renderClients(data);
                fillTicketClientSelect(data);
            } catch (err) {
                console.error(err);
                clientsListEl.innerHTML = "Не удалось загрузить клиентов";
            }
        }

        function renderClients(clients) {
            if (!clients.length) {
                clientsListEl.innerHTML = "<span style='color:#9ca3af;font-size:13px;'>Пока пусто. Добавь первого клиента 👇</span>";
                return;
            }

            clientsListEl.innerHTML = "";
            clients.forEach((c) => {
                const div = document.createElement("div");
                div.className = "client-item";
                div.innerHTML = `
                    <div class="name">${c.name}</div>
                    <div class="meta">
                        ${c.phone ? "📞 " + c.phone : ""} 
                        ${c.city ? " • " + c.city : ""} 
                        ${c.source ? " • " + c.source : ""}
                    </div>
                `;
                clientsListEl.appendChild(div);
            });
        }

        function fillTicketClientSelect(clients) {
            ticketClientSelect.innerHTML = '<option value="">Выбери клиента...</option>';
            clients.forEach((c) => {
                const opt = document.createElement("option");
                const phoneText = c.phone ? " • " + c.phone : "";
                const cityText = c.city ? " • " + c.city : "";
                opt.value = c.id;
                opt.textContent = `${c.name}${phoneText}${cityText}`;
                ticketClientSelect.appendChild(opt);
            });
        }

        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            statusEl.textContent = "";
            submitBtn.disabled = true;

            const payload = {
                name: document.getElementById("name").value.trim(),
                phone: document.getElementById("phone").value.trim() || null,
                city: document.getElementById("city").value.trim() || null,
                source: document.getElementById("source").value.trim() || null,
                tg_id: null
            };

            if (!payload.name) {
                statusEl.textContent = "Имя обязательно";
                submitBtn.disabled = false;
                return;
            }

            try {
                const res = await fetch(apiBase + "/clients", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                if (!res.ok) {
                    throw new Error("Ошибка при сохранении");
                }

                form.reset();
                statusEl.textContent = "Клиент сохранён ✅";

                await fetchClients();
                await fetchTickets();
            } catch (err) {
                console.error(err);
                statusEl.textContent = "Не удалось сохранить клиента";
            } finally {
                submitBtn.disabled = false;
                setTimeout(() => {
                    statusEl.textContent = "";
                }, 2000);
            }
        });

        // ==== ТИКЕТЫ ====

        async function fetchTickets() {
            ticketsListEl.innerHTML = "Загрузка...";
            try {
                let url = apiBase + "/tickets";
                if (currentStatusFilter) {
                    url += "?status=" + encodeURIComponent(currentStatusFilter);
                }
                const res = await fetch(url);
                if (!res.ok) {
                    throw new Error("Ошибка загрузки тикетов");
                }
                const data = await res.json();
                renderTickets(data);
            } catch (err) {
                console.error(err);
                ticketsListEl.innerHTML = "Не удалось загрузить обращения";
            }
        }

        function badgeClass(status) {
            switch (status) {
                case "new": return "badge badge-new";
                case "in_progress": return "badge badge-in_progress";
                case "waiting": return "badge badge-waiting";
                case "closed": return "badge badge-closed";
                default: return "badge badge-new";
            }
        }

        function statusLabel(status) {
            switch (status) {
                case "new": return "новое";
                case "in_progress": return "в работе";
                case "waiting": return "ждём клиента";
                case "closed": return "закрыто";
                default: return status;
            }
        }

        function renderTickets(tickets) {
            if (!tickets.length) {
                ticketsListEl.innerHTML = "<span style='color:#9ca3af;font-size:13px;'>Пока нет обращений. Создай тикет выше ☝️</span>";
                return;
            }

            ticketsListEl.innerHTML = "";
            tickets.forEach((t) => {
                const div = document.createElement("div");
                div.className = "ticket-item";
                const clientName = t.client?.name || ("Клиент #" + t.client_id);
                const comment = t.last_comment || "Без комментария";

                div.innerHTML = `
                    <div class="ticket-header">
                        <div class="title">${clientName}</div>
                        <div class="${badgeClass(t.status)}">${statusLabel(t.status)}</div>
                    </div>
                    <div class="meta">
                        Тип: ${t.type} • ${comment}
                    </div>
                    <div class="ticket-actions">
                        ${t.status !== "closed" ? '<button class="btn-secondary" onclick="closeTicket(' + t.id + ')">Закрыть</button>' : ""}
                    </div>
                `;
                ticketsListEl.appendChild(div);
            });
        }

        ticketForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            ticketStatusEl.textContent = "";
            ticketSubmitBtn.disabled = true;

            const clientId = parseInt(ticketClientSelect.value);
            if (!clientId) {
                ticketStatusEl.textContent = "Выбери клиента";
                ticketSubmitBtn.disabled = false;
                return;
            }

            const payload = {
                client_id: clientId,
                type: ticketTypeInput.value,
                last_comment: ticketCommentInput.value.trim() || null
            };

            try {
                const res = await fetch(apiBase + "/tickets", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                if (!res.ok) {
                    throw new Error("Ошибка при создании обращения");
                }

                ticketForm.reset();
                ticketStatusEl.textContent = "Обращение создано ✅";

                await fetchTickets();
            } catch (err) {
                console.error(err);
                ticketStatusEl.textContent = "Не удалось создать обращение";
            } finally {
                ticketSubmitBtn.disabled = false;
                setTimeout(() => {
                    ticketStatusEl.textContent = "";
                }, 2000);
            }
        });

        // смена фильтра статуса
        ticketFiltersEl.addEventListener("click", (e) => {
            const btn = e.target.closest(".filter-btn");
            if (!btn) return;

            currentStatusFilter = btn.dataset.status || "";

            ticketFiltersEl.querySelectorAll(".filter-btn").forEach((b) => {
                b.classList.toggle("active", b === btn);
            });

            fetchTickets();
        });

        // Глобальная функция, чтобы можно было вызвать из onclick
        async function closeTicketInternal(id) {
            try {
                const res = await fetch(apiBase + "/tickets/" + id + "/status", {
                    method: "PATCH",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ status: "closed" }),
                });
                if (!res.ok) {
                    throw new Error("Ошибка при смене статуса");
                }
                await fetchTickets();
            } catch (err) {
                console.error(err);
                alert("Не удалось сменить статус");
            }
        }
        window.closeTicket = closeTicketInternal;

        // стартовая загрузка
        fetchClients();
        fetchTickets();
    </script>
</body>
</html>
    """