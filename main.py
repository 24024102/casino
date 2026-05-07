import os
from fasthtml.common import *
import redis
import engine
import json
from urllib.parse import parse_qs

hub_name = os.getenv('HUB_NAME', 'Unknown Hub')
r = redis.Redis(host='redis', port=6379, decode_responses=True)
app, rt = fast_app(secret_key=os.getenv("SESSION_SECRET", "dev-only-fallback"))

hub_connections = {}

send_to_player  = {}   
BOT_NAMES = engine.BOT_NAMES
async def broadcast_to_hub(hub_id, message):
    if hub_id in hub_connections:
        dead = []
        for client_send in hub_connections[hub_id]:
            try:
                await client_send(message)
            except Exception:
                dead.append(client_send)
        for d in dead:
           hub_connections[hub_id].remove(d)
           send_to_player.pop(d, None)  


chat_script = Script("""
    function toggleChat() {
        const panel = document.getElementById('chat-panel');
        const isOpen = panel.style.right === '0px';
        panel.style.right = isOpen ? '-400px' : '0px';
    }
    // Auto-scroll chat to bottom
    const chatObs = new MutationObserver(() => {
        const msgs = document.getElementById('chat-messages');
        if (msgs) msgs.scrollTop = msgs.scrollHeight;
    });
    document.addEventListener('DOMContentLoaded', () => {
        const msgs = document.getElementById('chat-messages');
        if (msgs) chatObs.observe(msgs, { childList: true, subtree: true });
    });
""")
casino_style = Style("""
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@400;700;900&family=Crimson+Pro:ital,wght@0,300;0,400;1,300&display=swap');

    :root {
        --gold: #d4af37;
        --gold-light: #f0d060;
        --felt: #0a3d1f;
        --felt-light: #1b5e20;
        --dark: #0b0c10;
        --panel: #111418;
        --border: rgba(212,175,55,0.3);
        --text: #c5c6c7;
    }

    * { box-sizing: border-box; }
    body { background: var(--dark); color: var(--text); font-family: 'Crimson Pro', Georgia, serif; margin: 0; padding: 0; overflow-x: hidden; }

    /* ── LOBBY ── */
    .lobby-bg {
        min-height: 100vh; display: flex; align-items: center; justify-content: center;
        background: radial-gradient(ellipse at 30% 60%, #1a0a00 0%, #0b0c10 70%);
        position: relative; overflow: hidden;
    }
    .lobby-bg::before {
        content: '♠  ♥  ♦  ♣';
        position: absolute; font-size: 200px; color: rgba(212,175,55,0.03);
        letter-spacing: 40px; white-space: nowrap; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate(-15deg);
        font-family: 'Cinzel', serif; pointer-events: none;
    }
    .lobby-box {
        background: rgba(10, 12, 16, 0.97);
        border: 1px solid var(--border);
        border-top: 3px solid var(--gold);
        border-radius: 4px;
        padding: 60px 50px 50px;
        width: 420px;
        box-shadow: 0 40px 80px rgba(0,0,0,0.9), 0 0 60px rgba(212,175,55,0.08);
        position: relative;
    }
    .lobby-box::after {
        content: '';
        position: absolute; top: 0; left: 50%; transform: translateX(-50%);
        width: 60px; height: 3px;
        background: var(--gold);
    }
    .lobby-crest { font-size: 40px; margin-bottom: 10px; text-align: center; }
    .lobby-title {
        color: var(--gold); font-family: 'Cinzel', serif;
        font-size: 22px; font-weight: 900; letter-spacing: 6px;
        margin-bottom: 6px; text-align: center; text-transform: uppercase;
    }
    .lobby-subtitle {
        color: rgba(212,175,55,0.45); font-size: 12px; letter-spacing: 3px;
        text-align: center; margin-bottom: 40px; text-transform: uppercase;
    }
    .lobby-label { color: rgba(255,255,255,0.4); font-size: 11px; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 8px; display: block; }
    .lobby-input {
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
        border-bottom: 1px solid var(--gold); color: white; padding: 14px 16px;
        width: 100%; border-radius: 2px; font-size: 16px; font-family: 'Crimson Pro', serif;
        margin-bottom: 24px; transition: 0.3s; outline: none;
    }
    .lobby-input:focus { border-color: var(--gold); background: rgba(212,175,55,0.05); box-shadow: 0 4px 20px rgba(212,175,55,0.1); }
    .lobby-room-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 30px; }
    .lobby-room-card {
        border: 1px solid rgba(255,255,255,0.1); border-radius: 4px; padding: 14px 8px;
        text-align: center; cursor: pointer; transition: 0.25s; background: rgba(255,255,255,0.02);
        position: relative;
    }
    .lobby-room-card input[type=radio] { display: none; }
    .lobby-room-card:hover { border-color: var(--gold); background: rgba(212,175,55,0.06); }
    .lobby-room-card.selected { border-color: var(--gold); background: rgba(212,175,55,0.1); }
    .lobby-room-card .room-icon { font-size: 24px; margin-bottom: 6px; }
    .lobby-room-card .room-name { font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 2px; color: var(--gold); }
    .lobby-room-card .room-tag { font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 2px; }
    .lobby-btn {
        background: var(--gold); color: #000; font-family: 'Cinzel', serif;
        font-weight: 700; font-size: 13px; padding: 16px; width: 100%;
        border-radius: 2px; border: none; cursor: pointer; letter-spacing: 3px;
        text-transform: uppercase; transition: 0.3s;
    }
    .lobby-btn:hover { background: var(--gold-light); box-shadow: 0 8px 30px rgba(212,175,55,0.3); transform: translateY(-1px); }

    /* ── TOP NAV ── */
    .top-nav {
        background: rgba(10,10,14,0.98); padding: 0 30px;
        display: flex; justify-content: space-between; align-items: center;
        border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100;
        height: 60px; backdrop-filter: blur(10px);
    }
    .nav-brand { font-family: 'Cinzel', serif; color: var(--gold); font-size: 16px; letter-spacing: 4px; }
    .hub-links { display: flex; gap: 4px; }
    .hub-links a {
        color: rgba(255,255,255,0.4); text-decoration: none; padding: 8px 16px;
        font-family: 'Cinzel', serif; font-size: 11px; letter-spacing: 2px;
        text-transform: uppercase; transition: 0.2s; border-radius: 2px;
        border: 1px solid transparent;
    }
    .hub-links a:hover { color: var(--gold); border-color: var(--border); }
    .hub-links a.active { color: var(--gold); border-color: var(--gold); background: rgba(212,175,55,0.08); }
    .nav-profile { color: rgba(255,255,255,0.5); font-size: 13px; letter-spacing: 1px; }
    .nav-profile span { color: var(--gold); }

    /* ── TABLE ── */
    .page-wrap { padding: 30px 20px; min-height: calc(100vh - 60px); display: flex; flex-direction: column; align-items: center; gap: 20px; }
    .table-wood-rim {
        background: linear-gradient(135deg, #2a1505, #0d0600 60%, #1a0a02);
        border-radius: 200px; padding: 28px;
        box-shadow: 0 40px 80px rgba(0,0,0,0.95), inset 0 2px 4px rgba(255,255,255,0.05), 0 0 0 2px rgba(212,175,55,0.1);
        width: 100%; max-width: 1050px;
    }
    .table-felt {
        background: radial-gradient(ellipse at center, #1a5c2a 0%, var(--felt) 70%, #061008 100%);
        border-radius: 170px; padding: 50px 50px 40px;
        box-shadow: inset 0 0 100px rgba(0,0,0,0.8);
        display: flex; flex-direction: column; align-items: center;
        position: relative; min-height: 420px;
    }
    .phase-badge {
        position: absolute; top: 20px; left: 50%; transform: translateX(-50%);
        background: rgba(0,0,0,0.7); border: 1px solid var(--border);
        color: var(--gold); font-family: 'Cinzel', serif; font-size: 10px;
        letter-spacing: 3px; padding: 5px 16px; border-radius: 20px; text-transform: uppercase;
    }
    .players-row { display: flex; gap: 16px; justify-content: center; width: 100%; margin-bottom: 30px; flex-wrap: wrap; }
    .player-seat {
        background: rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.08);
        padding: 12px 20px; border-radius: 8px; text-align: center; min-width: 120px;
        transition: 0.3s; position: relative;
    }
    .player-seat.active { border-color: var(--gold); box-shadow: 0 0 20px rgba(212,175,55,0.3); }
    .player-seat.bot-seat { border-color: rgba(255,80,80,0.3); }
    .player-name { font-size: 13px; color: #aaa; margin-bottom: 4px; }
    .player-chips { font-family: 'Cinzel', serif; color: var(--gold); font-size: 15px; font-weight: 700; }
    .player-status { font-size: 10px; color: rgba(255,255,255,0.3); margin-top: 3px; letter-spacing: 1px; }

    .pot-display {
        font-family: 'Cinzel', serif; font-size: 26px; font-weight: 900;
        color: var(--gold); text-shadow: 0 0 20px rgba(212,175,55,0.5);
        margin-bottom: 20px; letter-spacing: 2px;
    }

    /* ── CARDS ── */
    .board-area { display: flex; justify-content: center; gap: 8px; min-height: 130px; margin-bottom: 30px; align-items: center; }
    .card {
        background: linear-gradient(135deg, #fff 0%, #f5f5f5 100%);
        border-radius: 8px; width: 80px; height: 115px;
        box-shadow: 3px 6px 20px rgba(0,0,0,0.7), inset 0 1px 0 rgba(255,255,255,0.8);
        display: inline-flex; flex-direction: column; justify-content: space-between;
        padding: 6px; font-family: 'Cinzel', serif; border: 1px solid #ddd;
        margin: 0; transition: transform 0.2s; position: relative;
        animation: cardDeal 0.3s ease-out;
    }
    @keyframes cardDeal { from { opacity: 0; transform: translateY(-20px) scale(0.9); } to { opacity: 1; transform: translateY(0) scale(1); } }
    .card:hover { transform: translateY(-12px) scale(1.05); z-index: 10; }
    .card.red { color: #c62828; }
    .card.black { color: #1a1a1a; }
    .card-top { font-size: 16px; font-weight: 700; line-height: 1; }
    .card-center { font-size: 38px; text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
    .card-bottom { font-size: 16px; font-weight: 700; line-height: 1; text-align: right; transform: rotate(180deg); }
    .card-back {
        background: linear-gradient(135deg, #1a237e, #283593);
        border-radius: 8px; width: 80px; height: 115px;
        box-shadow: 3px 6px 20px rgba(0,0,0,0.7);
        display: inline-flex; align-items: center; justify-content: center;
        font-size: 30px; border: 1px solid rgba(255,255,255,0.1);
    }

    /* ── ACTIONS ── */
    .my-hand-area { width: 100%; text-align: center; }
    .my-cards { display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }
    .action-bar { display: flex; gap: 12px; justify-content: center; align-items: center; flex-wrap: wrap; }
    .action-btn {
        color: white; padding: 13px 32px; border: none; border-radius: 3px;
        cursor: pointer; font-family: 'Cinzel', serif; font-weight: 700;
        font-size: 12px; letter-spacing: 2px; text-transform: uppercase;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5); transition: 0.15s;
        border-bottom: 3px solid rgba(0,0,0,0.3);
    }
    .btn-fold { background: linear-gradient(to bottom, #c62828, #8b1a1a); }
    .btn-call { background: linear-gradient(to bottom, #455a64, #263238); }
    .btn-raise { background: linear-gradient(to bottom, #2e7d32, #1b5e20); }
    .action-btn:hover { transform: translateY(-2px); filter: brightness(1.15); }
    .action-btn:active { transform: translateY(1px); filter: brightness(0.9); }

    /* ── DEALER LOG ── [NEW] */
    .dealer-log {
        background: rgba(0,0,0,0.5); border: 1px solid var(--border);
        border-radius: 4px; padding: 12px 18px; width: 100%; max-width: 1050px;
        font-size: 13px; color: rgba(212,175,55,0.8);
    }
    .dealer-log-title { font-family: 'Cinzel', serif; font-size: 10px; letter-spacing: 3px; color: rgba(212,175,55,0.4); margin-bottom: 8px; text-transform: uppercase; }
    .dealer-log-entry { padding: 3px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }

    /* ── CHAT ── */
    .chat-btn {
        position: fixed; bottom: 30px; right: 30px; z-index: 999;
        background: var(--gold); color: #000; border: none; border-radius: 50px;
        padding: 12px 22px; font-family: 'Cinzel', serif; font-size: 12px;
        letter-spacing: 2px; cursor: pointer; box-shadow: 0 8px 25px rgba(212,175,55,0.4);
        transition: 0.2s;
    }
    .chat-btn:hover { transform: translateY(-2px); background: var(--gold-light); }
    #chat-panel {
        position: fixed; top: 0; right: -400px; width: 360px; height: 100%;
        background: #0e1014; border-left: 1px solid var(--border);
        box-shadow: -10px 0 40px rgba(0,0,0,0.8);
        transition: right 0.3s ease; z-index: 1000;
        display: flex; flex-direction: column;
    }
    .chat-header {
        padding: 20px; border-bottom: 1px solid var(--border);
        font-family: 'Cinzel', serif; color: var(--gold); font-size: 13px; letter-spacing: 3px;
    }
    #chat-messages { flex: 1; overflow-y: auto; padding: 15px; display: flex; flex-direction: column; gap: 10px; }
    .msg-player { background: rgba(212,175,55,0.08); border-left: 2px solid var(--gold); padding: 8px 12px; border-radius: 0 4px 4px 0; font-size: 14px; }
    .msg-bot { background: rgba(255,80,80,0.06); border-left: 2px solid #c62828; padding: 8px 12px; border-radius: 0 4px 4px 0; font-size: 13px; color: #ccc; }
    .msg-dealer { background: rgba(0,150,0,0.08); border-left: 2px solid #2e7d32; padding: 8px 12px; border-radius: 0 4px 4px 0; font-size: 13px; color: #a5d6a7; }
""")



def PokerCard(rank, suit, color_class):
    return Div(
        Div(f"{rank}{suit}", cls="card-top"),
        Div(suit, cls="card-center"),
        Div(f"{rank}{suit}", cls="card-bottom"),
        cls=f"card {color_class}"
    )
def CardBack():
    return Div("🂠", cls="card-back")

@rt('/login')
def post(session, nickname: str, room_choice: str): 
    session['nickname'] = nickname
    session['room_id'] = room_choice
    return RedirectResponse('/', status_code=303)
@rt('/switch/{new_room}')
def switch_room(session, new_room: str):
    session['room_id'] = new_room
    return RedirectResponse('/', status_code=303)

@rt('/')
def get(session):
    if 'nickname' not in session:
        return Html(
            Head(Title("High Stakes Casino"), casino_style),
            Body(
                Div(
                    Div(
                        Div("♠", cls="lobby-crest"),
                        Div("HIGH STAKES", cls="lobby-title"),
                        Div("PRIVATE MEMBERS CLUB", cls="lobby-subtitle"),
                        Form(
                            Label("Your Alias", cls="lobby-label"),
                            Input(type="text", name="nickname", placeholder="e.g. The Shark...", required=True, cls="lobby-input"),
                            Label("Select Table", cls="lobby-label"),
                            # [NEW] Card-style room selector
                            Div(
                                Label(
                                    Input(type="radio", name="room_choice", value="Vegas", checked=True),
                                    Div("🎰", cls="room-icon"),
                                    Div("Las Vegas", cls="room-name"),
                                    Div("VIP", cls="room-tag"),
                                    cls="lobby-room-card selected", id="room-Vegas",
                                    onclick="selectRoom('Vegas')"
                                ),
                                Label(
                                    Input(type="radio", name="room_choice", value="Monaco"),
                                    Div("🎭", cls="room-icon"),
                                    Div("Monaco", cls="room-name"),
                                    Div("PRO", cls="room-tag"),
                                    cls="lobby-room-card", id="room-Monaco",
                                    onclick="selectRoom('Monaco')"
                                ),
                                Label(
                                    Input(type="radio", name="room_choice", value="Macau"),
                                    Div("🐉", cls="room-icon"),
                                    Div("Macau", cls="room-name"),
                                    Div("CLASSIC", cls="room-tag"),
                                    cls="lobby-room-card", id="room-Macau",
                                    onclick="selectRoom('Macau')"
                                ),
                                cls="lobby-room-grid"
                            ),
                            Button("ENTER THE CLUB →", type="submit", cls="lobby-btn"),
                            action="/login", method="post"
                        ),
                        cls="lobby-box"
                    ),
                    cls="lobby-bg"
                ),
                Script("""
                    function selectRoom(name) {
                        document.querySelectorAll('.lobby-room-card').forEach(el => el.classList.remove('selected'));
                        document.getElementById('room-' + name).classList.add('selected');
                        document.querySelector('input[value=' + name + ']').checked = true;
                    }
                """)
            )
        )

    nickname = session['nickname']
    room = session.get('room_id', 'Vegas')
    pot_key = f'room:{room}:pot'
    state_key = f'room:{room}:state'
    if not r.exists(state_key):
        init_state = engine.deal_preflop([nickname])
        r.set(state_key, json.dumps(init_state))
        r.set(pot_key, 0)
    state = json.loads(r.get(state_key))
    pot = r.get(pot_key) or "0"
    if nickname not in state.get('hands', {}):
        state['hands'][nickname] = []
        r.set(state_key, json.dumps(state))
    pot   = r.get(pot_key) or "0"
    phase = state.get('phase', 'preflop')
    player_slots = []
    for p, cards in state.get('hands', {}).items():
        if p in ('Toxic Senior', 'OOM-Killer'):
            folded = state.get('bot_folded', {}).get(p, False)
            player_slots.append(Div(
                Div(f"🤖 {p}", cls="player-name"),
                Div("$1,000", cls="player-chips"),
                Div("FOLDED" if folded else "IN HAND", cls="player-status"),
                cls="player-seat bot-seat"
            ))
        else:
            player_slots.append(Div(
                Div(f"👤 {p}", cls="player-name"),
                Div("$1,000", cls="player-chips"),
                Div("YOU" if p == nickname else "PLAYER", cls="player-status"),
                cls=f"player-seat {'active' if p == nickname else ''}"
            ))

    board_cards   = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('board', [])]
    my_hole_cards = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('hands', {}).get(nickname, [])]
    log_entries   = state.get('dealer_log', ['🃏 Dealer: Welcome to the table.'])
    if phase == 'showdown':
        action_buttons = Div(
            Form(
                Input(type="hidden", name="player", value=nickname), Input(type="hidden", name="move", value="restart"),
                Button("NEW ROUND 🔄", type="submit", cls="action-btn btn-new-round"),
                ws_send=True, cls="action-form"
            ),
            cls="action-bar", id="action-buttons-wrap"
        )
    else:
        action_buttons = Div(
            Form(Input(type="hidden", name="player", value=nickname), Input(type="hidden", name="move", value="fold"), 
                 Button("FOLD", type="submit", cls="action-btn btn-fold"), ws_send=True, cls="action-form"),
            Form(Input(type="hidden", name="player", value=nickname), Input(type="hidden", name="move", value="call"), 
                 Button("CALL", type="submit", cls="action-btn btn-call"), ws_send=True, cls="action-form"),
            Form(Input(type="hidden", name="player", value=nickname), Input(type="hidden", name="move", value="raise"), 
                 Button("RAISE", type="submit", cls="action-btn btn-raise"), ws_send=True, cls="action-form"),
            cls="action-bar", id="action-buttons-wrap"
        )
    top_nav = Div(
        Div("♠ CASINO NETWORK FIX-TEST", cls="nav-brand"),

        Div(
            A("Las Vegas", href="/switch/Vegas", cls="active" if room == "Vegas" else ""),
            A("Monaco",   href="/switch/Monaco", cls="active" if room == "Monaco" else ""),
            A("Macau",    href="/switch/Macau",  cls="active" if room == "Macau"  else ""),
            cls="hub-links"
        ),
        Div("Playing as: ", Span(nickname), cls="nav-profile"),
        cls="top-nav"
    )
    
    return Html(
        Head(
            Title(f"{room} — High Stakes"),
            Script(src="https://unpkg.com/htmx.org@2.0.2"),
            Script(src="https://unpkg.com/htmx-ext-ws@2.0.0/ws.js"),
            chat_script,
            casino_style
        ),
    Body(
            top_nav,
            Div(
               Div(
                    Div(phase.upper(), cls="phase-badge", id="phase-badge"),
                    Div(*player_slots, id="players-row", cls="players-row"),
                    Div(f"POT: ${pot}", id="pot-display", cls="pot-display"),
                    Div(*board_cards, id="board-cards", cls="board-area"),
                    Div(
                        Div(*my_hole_cards, cls="my-cards"),
                        action_buttons,
                        cls="my-hand-area"
                    ),
                    cls="table-felt"
                ),
                **{"hx-ext": "ws"},
                ws_connect=f"/ws/hub/{room}",
                cls="table-wood-rim"
            ),
            
            Div(
                Div("DEALER LOG", cls="dealer-log-title"),
                *[Div(e, cls="dealer-log-entry") for e in log_entries],
                id="dealer-log", cls="dealer-log"
            ),
            Button("💬 Chat", onclick="toggleChat()", cls="chat-btn"),
            Div(Div("ROOM CHAT", cls="chat-header"), Div(id="chat-messages"), id="chat-panel"),
            cls="page-wrap"

        )
    )

        
def parse_ws_form(msg):
    if isinstance(msg, bytes):
        msg = msg.decode()

    msg = (msg or "").strip()
    if not msg:
        return {}

    try:
        data = json.loads(msg)

        if isinstance(data, dict) and isinstance(data.get("body"), dict):
            data = data["body"]

        return data if isinstance(data, dict) else {}

    except (json.JSONDecodeError, TypeError):
        parsed = parse_qs(msg)
        return {k: v[0] if isinstance(v, list) and v else v for k, v in parsed.items()}


def ws_value(data, key, default=""):
    value = data.get(key, default)
    if isinstance(value, list):
        return value[0] if value else default
    return default if value is None else str(value)    
        


@app.ws('/ws/hub/{hub_id}')
async def ws_action(msg: str, send, hub_id: str):
    if isinstance(msg, bytes):
        msg = msg.decode()

    if hub_id not in hub_connections:
        hub_connections[hub_id] = []
    if send not in hub_connections[hub_id]:
        hub_connections[hub_id].append(send)

    data = parse_ws_form(msg)
    move = ws_value(data, 'move')
    player_name = ws_value(data, 'player', 'Anonymous')
    print(f"[WS PARSED] move={move} player={player_name} data={data}", flush=True)

    if not msg or msg.strip() == '':
        nickname = send_to_player.pop(send, None)
        if send in hub_connections.get(hub_id, []):
            hub_connections[hub_id].remove(send)
        if nickname:
            state_key = f'room:{hub_id}:state'
            raw = r.get(state_key)
            if raw:
                state = json.loads(raw)
                state.get('hands', {}).pop(nickname, None)
                r.set(state_key, json.dumps(state))
                note = Div(
                    Div(f"🚪 {nickname} left the table.", cls="dealer-log-entry"),
                    id="dealer-log", cls="dealer-log", hx_swap_oob="beforeend"
                )
                await broadcast_to_hub(hub_id, to_xml(note))
        return
    try:
        if not move:
            return
        send_to_player[send] = player_name
        pot_key   = f'room:{hub_id}:pot'
        state_key = f'room:{hub_id}:state'
        pot       = int(r.get(pot_key) or "0")
        raw = r.get(state_key)
        if not raw:
            return
        game_state = json.loads(raw)
        if move == 'restart':
            humans    = [p for p in game_state.get('hands', {}) if p not in BOT_NAMES]
            new_state = engine.deal_preflop(humans)
            r.set(state_key, json.dumps(new_state))
            r.set(pot_key, 0)
            await broadcast_to_hub(hub_id, '<div id="action-buttons-wrap" hx-swap-oob="true"><script>window.location.reload();</script></div>')
            return
        bot_phrases  = []
        update_board = ""
        update_board = ""
        advance_phase = False

        if move == 'fold':
            game_state.setdefault('dealer_log', []).append(f"🃏 {player_name} folds.")
            game_state.setdefault('human_folded', {})[player_name] = True
            game_state['phase'] = 'showdown'
            game_state['dealer_log'].append("🃏 Dealer: Player folded. Round is over.")

        elif move == 'call':
            pot = r.incrby(pot_key, 50)
            game_state.setdefault('dealer_log', []).append(f"🃏 {player_name} calls $50.")
            advance_phase = True

        elif move == 'raise':
            pot = r.incrby(pot_key, 100)
            game_state.setdefault('dealer_log', []).append(f"🃏 {player_name} raises $100.")
            advance_phase = True

        else:
            return

        bot_folded = game_state.get('bot_folded', {b: False for b in BOT_NAMES})

        if game_state.get('phase') != 'showdown':
            for bot_name in BOT_NAMES:
                if bot_folded.get(bot_name):
                    continue

                bot_cards = game_state.get('hands', {}).get(bot_name, [])
                board_cards = game_state.get('board', [])
                result = engine.bot_decide_move(bot_name, bot_cards, board_cards, pot, 50)

                if result['move'] == 'fold':
                    bot_folded[bot_name] = True
                    game_state['dealer_log'].append(f"🃏 {bot_name} folds.")
                elif result['move'] == 'raise':
                    pot = r.incrby(pot_key, 100)
                    game_state['dealer_log'].append(f"🃏 {bot_name} raises $100.")
                else:
                    pot = r.incrby(pot_key, 50)
                    game_state['dealer_log'].append(f"🃏 {bot_name} calls.")

        game_state['bot_folded'] = bot_folded

        if advance_phase and game_state.get('phase') != 'showdown':
            game_state = engine.deal_next_phase(game_state)

        game_state['dealer_log'] = game_state['dealer_log'][-10:]
        r.set(state_key, json.dumps(game_state))

        board_html = [PokerCard(c['rank'], c['suit'], c['color']) for c in game_state.get('board', [])]
        update_board = Div(*board_html, id="board-cards", cls="board-area", hx_swap_oob="true")

        game_state['bot_folded'] = bot_folded
        game_state['dealer_log'] = game_state['dealer_log'][-10:]
        r.set(state_key, json.dumps(game_state))
        current_phase = game_state.get('phase', 'preflop')
        update_pot    = Div(f"POT: ${r.get(pot_key)}", id="pot-display", cls="pot-display", hx_swap_oob="true")
        update_phase  = Div(current_phase.upper(), cls="phase-badge", id="phase-badge", hx_swap_oob="true")
        update_log    = Div(
            Div("DEALER LOG", cls="dealer-log-title"),
            *[Div(e, cls="dealer-log-entry") for e in game_state.get('dealer_log', [])],
            id="dealer-log", cls="dealer-log", hx_swap_oob="true"
        )
        parts = [
            to_xml(update_pot),
            to_xml(update_phase),
            to_xml(update_log),
        ]

        if current_phase == 'showdown':
            new_buttons = Div(
                Form(
                    Input(type="hidden", name="move", value="restart"),
                    Button("NEW ROUND 🔄", type="submit", cls="action-btn"),
                    ws_send=True,
                ),
                cls="action-bar",
                id="action-buttons-wrap",
                hx_swap_oob="true"
            )
            parts.append(to_xml(new_buttons))

        if update_board:
            parts.append(to_xml(update_board))

        await broadcast_to_hub(hub_id, "".join(parts))

    except Exception as e:
        print(f"[WS ERROR] {e}")


if __name__ == '__main__':
    serve(host='0.0.0.0', port=5001)
