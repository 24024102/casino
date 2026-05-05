import os
from fasthtml.common import *
import redis
import engine
import json

hub_name = os.getenv('HUB_NAME', 'Unknown Hub')
r = redis.Redis(host='redis', port=6379, decode_responses=True)
app, rt = fast_app(secret_key="1234")
hub_connections = {}
async def broadcast_to_hub(hub_id, message):
    if hub_id in hub_connections:
        for client_send in hub_connections[hub_id]:
            try:
                await client_send(message)
            except Exception:
                pass

def init_hub(hub_id):
    if not r.exists(f'hub:{hub_id}:pot'):
        r.set(f'hub:{hub_id}:pot', 0)
    if not r.exists(f'hub:{hub_id}:hand'):
        r.set(f'hub:{hub_id}:hand', json.dumps(engine.deal_new_round()))
casino_style = Style("""
    body { background-color: #0b0f19; color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    
    /* Анимации мастей на фоне */
    .bg-animation { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: -1; overflow: hidden; background: radial-gradient(circle, #1a1a2e 0%, #0b0b12 100%); }
    .suit { position: absolute; font-size: 60px; color: rgba(255, 255, 255, 0.03); animation: floatUp 15s linear infinite; bottom: -100px; }
    .suit.red { color: rgba(217, 32, 32, 0.05); }
    @keyframes floatUp { 0% { transform: translateY(0) rotate(0deg); opacity: 0; } 10% { opacity: 1; } 90% { opacity: 1; } 100% { transform: translateY(-110vh) rotate(360deg); opacity: 0; } }
    .suit:nth-child(1) { left: 10%; animation-duration: 12s; }
    .suit:nth-child(2) { left: 30%; animation-duration: 18s; animation-delay: 3s; font-size: 80px; }
    .suit:nth-child(3) { left: 50%; animation-duration: 14s; animation-delay: 6s; }
    .suit:nth-child(4) { left: 70%; animation-duration: 20s; animation-delay: 1s; font-size: 90px; }
    .suit:nth-child(5) { left: 90%; animation-duration: 16s; animation-delay: 4s; }

    /* Меню логина (Glassmorphism) */
    .login-container { background: rgba(20, 20, 25, 0.85); backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 40px; max-width: 450px; margin: 150px auto; text-align: center; box-shadow: 0 0 40px rgba(0, 255, 128, 0.1); }
    .login-input { background: rgba(0, 0, 0, 0.5); border: 1px solid #444; color: #00ff88; padding: 15px; width: 80%; border-radius: 10px; font-size: 18px; margin-bottom: 25px; outline: none; transition: all 0.3s ease; }
    .login-input:focus { border-color: #00ff88; box-shadow: 0 0 15px rgba(0, 255, 128, 0.3); }
    .login-btn { background: linear-gradient(45deg, #2b7a2b, #1e5c1e); color: white; padding: 15px 30px; border: none; border-radius: 10px; font-size: 18px; font-weight: bold; cursor: pointer; box-shadow: 0 5px 15px rgba(0,0,0,0.5); transition: transform 0.2s; }
    .login-btn:hover { transform: scale(1.05); }

    /* Стол и карты */
    .poker-table { background: radial-gradient(circle, #2e7a48 0%, #11381f 100%); border: 25px solid #3e2723; border-radius: 200px; box-shadow: inset 0 0 50px rgba(0,0,0,0.8), 0 20px 50px rgba(0,0,0,0.9); padding: 50px; max-width: 1000px; margin: 40px auto; position: relative; }
    .card { background: white; border-radius: 8px; width: 80px; height: 115px; box-shadow: 2px 5px 15px rgba(0,0,0,0.4); display: inline-flex; flex-direction: column; justify-content: space-between; padding: 5px; font-family: 'Times New Roman', serif; border: 1px solid #ddd; margin: 0 -10px; transition: transform 0.2s; }
    .card:hover { transform: translateY(-10px); z-index: 10; }
    .card.red { color: #d92020; }
    .card.black { color: #111; }
    .card-top { font-size: 18px; font-weight: bold; line-height: 1; text-align: left; }
    .card-center { font-size: 36px; text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center; }
    .card-bottom { font-size: 18px; font-weight: bold; line-height: 1; text-align: right; transform: rotate(180deg); }
    
    .player-seat { background: rgba(0,0,0,0.6); border: 2px solid #555; padding: 15px 25px; border-radius: 50px; text-align: center; min-width: 120px; box-shadow: 0 5px 15px rgba(0,0,0,0.5); }
    .player-seat.active { border-color: #f0ad4e; box-shadow: 0 0 20px rgba(240, 173, 78, 0.5); }
    
    /* Чат */
    #chat-panel { position: fixed; top: 0; right: -400px; width: 350px; height: 100%; background: #252526; border-left: 1px solid #333; box-shadow: -10px 0 30px rgba(0,0,0,0.8); transition: right 0.3s cubic-bezier(0.4, 0.0, 0.2, 1); z-index: 1000; display: flex; flex-direction: column; }
    #chat-panel.open { right: 0; }
    .chat-header { background: #1e1e1e; padding: 20px; font-size: 18px; font-weight: bold; border-bottom: 1px solid #333; display: flex; justify-content: space-between; }
    #chat-messages { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    .chat-btn { position: fixed; bottom: 30px; right: 30px; background: #007acc; color: white; border: none; border-radius: 50px; padding: 15px 25px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(0,122,204,0.4); z-index: 1001; transition: background 0.2s; }
    .chat-btn:hover { background: #005f9e; }
    .msg-bot { background: #3a1c1c; border-left: 4px solid #d9534f; padding: 10px; border-radius: 4px; font-size: 14px; }
    .msg-player { background: #1c2b3a; border-right: 4px solid #5bc0de; padding: 10px; border-radius: 4px; font-size: 14px; text-align: right; }
""")

chat_script = Script("""
    function toggleChat() { document.getElementById('chat-panel').classList.toggle('open'); }
""")
def BackgroundAnimations():
    return Div(Div("♠", cls="suit"), Div("♥", cls="suit red"), Div("♣", cls="suit"), Div("♦", cls="suit red"), Div("♠", cls="suit"), cls="bg-animation")

def PokerCard(rank, suit, color_class):
    return Div(
        Div(f"{rank}{suit}", cls="card-top"),
        Div(suit, cls="card-center"),
        Div(f"{rank}{suit}", cls="card-bottom"),
        cls=f"card {color_class}"
    )
@rt('/login')
def post(session, nickname: str):
    session['nickname']=nickname
    return RedirectResponse('/', status_code=303)


@rt('/')
def get(session):
    if 'nickname' not in session:
        return Html(
            Head(Title("Login | Casino"), casino_style),
            Body(
                Div(
                    H2(f"Welcome to {hub_name}"),
                    P("Identify yourself to join the table:", style="color: #888;"),
                    Form(
                        Input(type="text", name="nickname", placeholder="Enter your hacker name...", required=True, style="padding: 10px; width: 80%; margin-bottom: 20px; border-radius: 5px; border: 1px solid #555; background: #222; color: white; font-size: 16px;"),
                        Br(),
                        Button("Join Table", type="submit", style="background: #2b7a2b; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 16px;"),
                        action="/login", method="post"
                    ),
                    style="text-align: center; margin: 100px auto; padding: 50px; background: #111; border: 2px solid #333; border-radius: 10px; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.8);"
                )
            )
        )
    nickname = session['nickname']
    visits = r.incr('visits')
    pot_key = f'hub:{hub_name}:pot_v2'
    if not r.exists(pot_key):
        r.set(pot_key, 0)
    pot = r.get(pot_key)
    raw_hand = r.get('game_state_v2')
    if not raw_hand:
       new_hand = engine.deal_preflop([nickname])
       raw_hand = json.dumps(new_hand)
       r.set('current_hand', raw_hand)
    hand = json.loads(str(raw_hand))
    board_html = [PokerCard(c['rank'], c['suit'], c['color']) for c in hand['board']]
    my_cards_html = [PokerCard(c['rank'], c['suit'], c['color']) for c in hand['hands'].get(nickname, [])]
    fold_vals = json.dumps({"move": "fold", "player": nickname})
    call_vals = json.dumps({"move": "call", "player": nickname})
    raise_vals = json.dumps ({ "move": "raise", "player": nickname})
    return Html(
        Head(
            Title(f"Casino | {hub_name}"), 
            Script(src="https://unpkg.com/htmx.org@2.0.2"), 
            casino_style, 
            chat_script
        ),
        Body(
            Div(
                H2(f"♠️ {hub_name} Cluster ♣️", style="margin:0; color: #d4af37; letter-spacing: 2px;"),
            P(f"Total connections: {visits} | DB Ping: 2ms", style="margin:5px 0 0 0; font-size: 12px; color: #888;"),
             style="text-align: center; padding: 20px; background: #111; border-bottom: 1px solid #333;"
            ),
            
            Div(
                Div(
                    Div(Div("Bot OOM-Killer", style="font-size: 12px; color: #aaa;"), Div("$1200", style="font-weight: bold;"), cls="player-seat"),
                Div(Div("SysAdmin", style="font-size: 12px; color: #aaa;"), Div("House Bank", style="font-weight: bold; color: #d4af37;"), cls="player-seat"),
                  Div(Div("Toxic Senior", style="font-size: 12px; color: #aaa;"), Div("$850", style="font-weight: bold;"), cls="player-seat"),
                style="display: flex; justify-content: space-around; margin-bottom: 40px; transform: translateY(-30px);"
                ),
                
                Div(
                  Div(f"POT: ${pot}", id="pot-display", style="font-size: 28px; font-weight: bold; color: #d4af37; background: rgba(0,0,0,0.5); padding: 5px 20px; border-radius: 20px; display: inline-block; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);"),
                  Br(),
                  PokerCard("A", "♠", "black"),
                  PokerCard("K", "♥", "red"),
                  PokerCard("10", "♦", "red"),
              PokerCard("J", "♠", "black"),
                 PokerCard("Q", "♣", "black"),
            style="text-align: center; margin-bottom: 40px;"
                ),
                
                Div(
                    Div(Div("👤 {nickname}", style="font-size: 12px; color: #aaa;"), Div("$1000", style="font-weight: bold;"), cls="player-seat active", style="margin: 0 auto 20px auto; width: fit-content;"),
                    Div(*my_cards_html, style="margin-bottom: 20px;"),
                    Form(
                        Input(type="hidden", name="player", value=nickname),
                        Button("FOLD", type="submit", onclick="this.form.move.value='fold'", style="background: #a83232; color: white; padding: 12px 30px; border: none; border-radius: 4px; margin: 5px; cursor: pointer; font-weight: bold;"),
                        Button("CALL", type="submit", onclick="this.form.move.value='call'", style="background: #4a4a4a; color: white; padding: 12px 30px; border: none; border-radius: 4px; margin: 5px; cursor: pointer; font-weight: bold;"),
                        Button("RAISE", type="submit", onclick="this.form.move.value='raise'", style="background: #2b7a2b; color: white; padding: 12px 30px; border: none; border-radius: 4px; margin: 5px; cursor: pointer; font-weight: bold;"),
                        Input(type="hidden", name="move", value=""), # Сюда подставится значение кнопки
                        hx_ext="ws", ws_connect=f"/ws/hub/{hub_name}", ws_send=True, hx_swap="none", # hx_swap="none" спасает от исчезновения
                        style="text-align: center; transform: translateY(30px);"
                    )
                ),
                cls="poker-table"
            ),
            
            Button("💬 Open Terminal (Chat)", onclick="toggleChat()", cls="chat-btn"),
            
            Div(
                Div("Table Terminal", Span("✕", onclick="toggleChat()", style="cursor: pointer; color: #888;"), cls="chat-header"),
                Div(
                Div(Div("SysAdmin:", style="color: #888; font-size: 11px;"), "Welcome to the cluster. Blinds are 10/20. Don't forget to commit your chips.", cls="msg-bot"),
                id="chat-messages"
                ),
                id="chat-panel"
            )
        )
    )

@app.ws('/ws/hub/{hub_id}')
async def ws_action(msg: str, send, hub_id: str):
    if hub_id not in hub_connections:
        hub_connections[hub_id] = []
    if send not in hub_connections[hub_id]:
        hub_connections[hub_id].append(send)
    try:
        data = json.loads(msg)
        move = data.get('move')
        player_name = data.get('player', 'Anonymus')
        if not move:
            return  
        pot_key = f'hub:{hub_id}:pot_v2'
        pot = int(r.get(pot_key) or "0")
        bot_response = ""
        update_board = ""
        if move == 'fold':
            bot_response = "Toxic Senior: Folding already? Your uptime is worse than AWS us-east-1. 📉"
        elif move == 'call':
            pot = r.incrby(pot_key, 50)
            
            bot_response = "Bot OOM-Killer: Just a call? I can read your bluff like a plain-text .env file. 🤡"
            game_state = json.loads(r.get('game_state_v2'))
            updated_state = engine.deal_next_phase(game_state)
            r.set('game_state_v2', json.dumps(updated_state))
            board_html = [PokerCard(c['rank'], c['suit'], c['color']) for c in updated_state['board']]
            update_board = Div(*board_html, id="board-cards", hx_swap_oob="innerHTML")       
        elif move == 'raise':
            pot = r.incrby(pot_key, 100)
            bot_response = "Toxic Senior: Oh, scaling up? Bro is deploying to production on a Friday... I respect the reckless raise. 🚀"
        update_pot = Div(f"POT: ${pot}", id="pot-display", hx_swap_oob="true", style="font-size: 28px; font-weight: bold; color: #d4af37; background: rgba(0,0,0,0.5); padding: 5px 20px; border-radius: 20px; display: inline-block; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);")
        chat_update = Div(
            Div(Div(f"{player_name}:", style="color: #5bc0de; font-size: 11px;"), f"Executed: {move.upper()}", cls="msg-player"),
            Div(Div("System:", style="color: #d9534f; font-size: 11px;"), bot_response, cls="msg-bot"),
            id="chat-messages", hx_swap_oob="beforeend"
        )
        html_to_send = f"{update_pot}{chat_update}{update_board}"
        await broadcast_to_hub(hub_id, html_to_send)
        
    finally:
        pass
