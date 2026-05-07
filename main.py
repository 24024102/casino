import os
import asyncio
from fasthtml.common import *
import redis
import engine
import json
from urllib.parse import quote, unquote


hub_name = os.getenv('HUB_NAME', 'Unknown Hub')
r = redis.Redis(host='redis', port=6379, decode_responses=True)
app, rt = fast_app(
    secret_key=os.getenv("SESSION_SECRET", "dev-only-fallback"),
    exts='ws'
)

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
RAISE_AMOUNT = 100
BOT_THINK_SECONDS = 0.8
def ActionButtons(player_name, state, oob=False):
    attrs = {"cls": "action-bar", "id": "action-buttons-wrap"}
    if oob:
        attrs["hx_swap_oob"] = "true"

    if state.get('phase') == 'showdown':
        return Div(
            Button("NEW ROUND 🔄", type="button", cls="action-btn btn-new-round",
                   ws_send=True, hx_vals=json.dumps({"move": "restart"})),
            **attrs
        )

    if player_name not in state.get('hands', {}):
        return Div(Div("WAITING NEXT ROUND", cls="turn-note"), **attrs)

    if state.get('current_turn') != player_name:
        return Div(
            Div(f"WAITING: {state.get('current_turn', 'dealer')}", cls="turn-note"),
            Button("FOLD", type="button", cls="action-btn btn-fold", disabled=True),
            Button("CALL", type="button", cls="action-btn btn-call", disabled=True),
            Button("RAISE", type="button", cls="action-btn btn-raise", disabled=True),
            **attrs
        )

    needed = max(0, int(state.get('current_bet', 0)) - int(state.get('street_bets', {}).get(player_name, 0)))
    call_label = "CHECK" if needed == 0 else f"CALL ${needed}"

    return Div(
        Button("FOLD", type="button", cls="action-btn btn-fold", ws_send=True, hx_vals=json.dumps({"move": "fold"})),
        Button(call_label, type="button", cls="action-btn btn-call", ws_send=True, hx_vals=json.dumps({"move": "call"})),
        Button(f"RAISE ${RAISE_AMOUNT}", type="button", cls="action-btn btn-raise", ws_send=True, hx_vals=json.dumps({"move": "raise"})),
        **attrs
    )
def room_state_key(room):return f'room:{room}:state'
def room_pot_key(room): return f'room:{room}:pot'
def save_state(room,state):
    r.set(room_state_key(room), json.dumps(state))
    r.set(room_pot_key(room), int(state.get('pot', 0 )))
def active_players(state):
    return [ p for p in state.get('hands', {}) if not state.get('folded', {}).get(p, False)]
def players_needing_action(state):
    if state.get('phase') == 'showdown': return []
    active = active_players(state)
    if len(active) <= 1: return[]
    current_bet = int(state.get('current_bet', 0))
    return [
        p for p in active
        if not state.get('acted', {}).get(p, False)
        or int(state.get('street_bets', {}).get(p, 0)) < current_bet
    ]
def first_player_needing_action(state, after=None):
    need = set(players_needing_action(state))
    order = list(state.get('hands', {}).keys())
    if not need or not order: return None
    start = (order.index(after) + 1) % len(order) if after in order else 0
    for i in range(len(order)):
        p = order[(start + i) % len(order)]
        if p in need: return p
    return None

def reset_betting_round(state):
    players = list(state.get('hands', {}).keys())
    state['current_bet'] = 0
    state['raises_this_street'] = 0
    state['street_bets'] = {p: 0 for p in players}
    state['acted'] = {p: False for p in players}
    state['current_turn'] = first_player_needing_action(state, after=state.get('dealer_button'))

SMALL_BLIND = 50
BIG_BLIND = 100
MAX_RAISES_PER_STREET = 1
def pay_to_pot(state, player,amount):
    amount = max(0,int(amount))
    chips = state.setdefault('chips',{}.setdefault(player, 1000))
    paid = min(chips, amount)
    state['chips']['player'] = chips - paid
    state['pot'] = int(state.get('pot', 0)) + paid
    state.setdefault('street_bets', {}).setdefault(player, 0)
    state['street_bets'][player] += paid

def new_game_state(humans, previous_dealer=None):
    humans = list(dict.fromkeys([p for p in humans if p and p not in BOT_NAMES]))
    state = engine.deal_preflop(humans)
    players = list(state.get('hands', {}).keys())

    dealer_i = 0
    if previous_dealer in players:
        dealer_i = (players.index(previous_dealer) + 1) % len(players)

    dealer = players[dealer_i]
    sb = players[(dealer_i + 1) % len(players)]
    bb = players[(dealer_i + 2) % len(players)]

    state['pot'] = 0
    state['chips'] = {p: 1000 for p in players}
    state['folded'] = {p: False for p in players}
    state['street_bets'] = {p: 0 for p in players}
    state['acted'] = {p: False for p in players}
    state['current_bet'] = BIG_BLIND
    state['raises_this_street'] = 0
    state['dealer_button'] = dealer
    state['waiting_players'] = []
    state['winners'] = []

    pay_to_pot(state, sb, SMALL_BLIND)
    pay_to_pot(state, bb, BIG_BLIND)

    state['current_turn'] = first_player_needing_action(state, after=bb)
    state['dealer_log'] = [
        '🃏 Dealer: New hand started.',
        f'🟡 Dealer button: {dealer}.',
        f'🃏 {sb} posts small blind ${SMALL_BLIND}.',
        f'🃏 {bb} posts big blind ${BIG_BLIND}.',
    ]
    return state

def render_player_slots(state, viewer=None):
    slots = []
    for p in state.get('hands', {}):
        folded = state.get('folded', {}).get(p, False)
        if folded:
            status = "FOLDED"
        elif p == state.get('current_turn'):
            status = "TURN"
        elif p == viewer:
            status = "YOU"
        elif p in BOT_NAMES:
            status = "BOT"
        else:
            status = "WAITING"
        slots.append(Div(
            Div(("🤖 " if p in BOT_NAMES else "👤 ") + p, cls="player-name"),
            Div(f"${state.get('chips', {}).get(p, 1000):,}", cls="player-chips"),
            Div(status, cls="player-status"),
            cls=f"player-seat {'bot-seat' if p in BOT_NAMES else ''} {'active' if p == state.get('current_turn') else ''}"
        ))
    return slots
def advance_turn_after_action(state, after_player):
    if len(active_players(state)) <= 1:
        state['phase'] = 'showdown'
        state['current_turn'] = None
        state['dealer_log'].append(f"Dealer:{active_players(state)[0]}wins")
        return
    nxt = first_player_needing_action(state, after=after_player)
    if nxt:
        state['current_turn'] = nxt
        return
    if state.get('phase') == 'river':
        state['phase'] = 'showdown'
        state['current_turn'] = None
        state['dealer_log'].append("Dealer:SHOWDOWN")
    else:
        engine.deal_next_phase(state)
        reset_betting_round(state)
def apply_move_to_state(state, player_name, move, phrase=None):
    state.setdefault('dealer_log', [])
    if move == 'fold':
        state['folded'][player_name] = True
        state['acted'][player_name] = True
        state['dealer_log'].append(f"🃏 {player_name} folds.")
    elif move == 'call':
        needed = max(0, state['current_bet'] - state['street_bets'].get(player_name, 0))
        paid = pay_to_pot(state, player_name, needed)
        state['acted'][player_name] = True
        state['dealer_log'].append(f"🃏 {player_name} {'checks' if paid == 0 else f'calls ${paid}'}.")
    elif move == 'raise':
        if state.get('raises_this_street', 0) >= MAX_RAISES_PER_STREET:
            return apply_move_to_state(state, player_name, 'call', phrase)
        state['current_bet'] += RAISE_AMOUNT
        needed = state['current_bet'] - state['street_bets'].get(player_name, 0)
        paid = pay_to_pot(state, player_name, needed)
        state['acted'][player_name] = True
        state['raises_this_street'] = state.get('raises_this_street', 0) + 1
        state['dealer_log'].append(f"🃏 {player_name} raises +${RAISE_AMOUNT}.")
    if phrase:
        state['dealer_log'].append(f"💬 {phrase}")
    advance_turn_after_action(state, player_name)
async def run_bot_turns(state):
    while state.get('phase') != 'showdown' and state.get('current_turn') in BOT_NAMES:
        bot_name = state['current_turn']
        await asyncio.sleep(BOT_THINK_SECONDS)
        needed = max(0, state['current_bet'] - state['street_bets'].get(bot_name, 0))
        result = engine.bot_decide_move(
            bot_name,
            state.get('hands', {}).get(bot_name, []),
            state.get('board', []),
            state.get('pot', 0),
            needed
        )
        move = result.get('move', 'call')
        if needed == 0 and move == 'fold':
            move = 'call'

        if move not in ('fold', 'call', 'raise'):
            move = 'call'
        apply_move_to_state(state, bot_name, move, result.get('phrase'))

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
    
    raw = r.get(room_state_key(room))
    if raw:
        state = json.loads(raw)
        if 'current_turn' not in state or 'folded' not in state:
            state = new_game_state([nickname])
    else:
        state = new_game_state([nickname])
    if nickname not in state.get('hands', {}) and nickname not in state.get('waiting_players', []):
        state.setdefault('waiting_players', []).append(nickname)
        state.setdefault('dealer_log', []).append(f" Dealer: {nickname} joined next round.")
    save_state(room, state)
    pot = state.get('pot', 0)
    phase = state.get('phase', 'preflop')
    player_slots = render_player_slots(state, nickname)
    board_cards   = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('board', [])]
    my_hole_cards = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('hands', {}).get(nickname, [])]
    log_entries   = state.get('dealer_log', ['🃏 Dealer: Welcome to the table.'])
    action_buttons = ActionButtons(nickname, state)
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
                        Div(*my_hole_cards, id="my-cards", cls="my-cards"),
                        action_buttons,
                        cls="my-hand-area"
                    ),
                    cls="table-felt"
                ),
                **{"hx-ext": "ws"},
                ws_connect=f"/ws/hub/{room}/{quote(nickname, safe='')}",

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
def table_update(state, player_name):
    board_cards = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('board', [])]
    my_cards = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('hands', {}).get(player_name, [])]

    return (
        Div(state.get('phase', 'preflop').upper(), cls="phase-badge", id="phase-badge", hx_swap_oob="true"),
        Div(*render_player_slots(state, player_name), id="players-row", cls="players-row", hx_swap_oob="true"),
        Div(f"POT: ${state.get('pot', 0)}", id="pot-display", cls="pot-display", hx_swap_oob="true"),
        Div(*board_cards, id="board-cards", cls="board-area", hx_swap_oob="true"),
        Div(*my_cards, id="my-cards", cls="my-cards", hx_swap_oob="true"),
        Div(Div("DEALER LOG", cls="dealer-log-title"),
            *[Div(e, cls="dealer-log-entry") for e in state.get('dealer_log', [])],
            id="dealer-log", cls="dealer-log", hx_swap_oob="true"),
        ActionButtons(player_name, state, oob=True),
    )

@app.ws('/ws/hub/{hub_id}/{player_name}')
async def ws_action(data: dict, send, hub_id: str, player_name: str):
    
    player_name = unquote(player_name)
    move = data.get('move', '')
    raw = r.get(room_state_key(hub_id))
    if not raw: return
    state = json.loads(raw)
    if move == 'restart':
        humans = [p for p in state.get('hands', {}) if p not in BOT_NAMES]
        humans += state.get('waiting_players', [])
        state = new_game_state(humans, previous_dealer=state.get('dealer_button'))
        save_state(hub_id, state)
        return table_update(state, player_name)

    if state.get('phase') == 'showdown':
        return ActionButtons(player_name, state, oob=True)
    if player_name != state.get('current_turn'):
        return ActionButtons(player_name, state, oob=True)
    if move not in ('fold', 'call', 'raise'):
        return
    if player_name != state.get('current_turn'):
     return ActionButtons(player_name, state, oob=True)
    state['dealer_log'] = state['dealer_log'][-10:]
    save_state(hub_id, state)
    apply_move_to_state(state, player_name, move)
    await run_bot_turns(state)
    board_cards = [PokerCard(c['rank'], c['suit'], c['color']) for c in state.get('board', [])]
    return (
        Div(state.get('phase', 'preflop').upper(), cls="phase-badge", id="phase-badge", hx_swap_oob="true"),
        Div(*render_player_slots(state, player_name), id="players-row", cls="players-row", hx_swap_oob="true"),
        Div(f"POT: ${state.get('pot', 0)}", id="pot-display", cls="pot-display", hx_swap_oob="true"),
        Div(*board_cards, id="board-cards", cls="board-area", hx_swap_oob="true"),
        Div(Div("DEALER LOG", cls="dealer-log-title"),
            *[Div(e, cls="dealer-log-entry") for e in state.get('dealer_log', [])],
            id="dealer-log", cls="dealer-log", hx_swap_oob="true"),
        ActionButtons(player_name, state, oob=True),
    )

if __name__ == '__main__':
    serve(host='0.0.0.0', port=5001)
