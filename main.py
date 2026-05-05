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
        


casino_style = Style("""
    body { background-color: #0b0c10; color: #c5c6c7; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; overflow-x: hidden; }
    
    
    .lobby-bg { background: url('https://www.transparenttextures.com/patterns/stardust.png'), radial-gradient(circle at center, #1f2833 0%, #0b0c10 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
    .lobby-box { background: rgba(11, 12, 16, 0.85); backdrop-filter: blur(20px); border: 1px solid rgba(102, 252, 241, 0.2); border-radius: 15px; padding: 50px; width: 100%; max-width: 400px; box-shadow: 0 20px 50px rgba(0,0,0,0.8), 0 0 30px rgba(102, 252, 241, 0.1); text-align: center; }
    .lobby-title { color: #66fcf1; font-size: 32px; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 3px; font-weight: 800; }
    .lobby-input { background: rgba(255,255,255,0.05); border: 1px solid #45a29e; color: white; padding: 15px; width: 100%; box-sizing: border-box; border-radius: 8px; font-size: 16px; margin-bottom: 20px; transition: 0.3s; }
    .lobby-input:focus { outline: none; border-color: #66fcf1; box-shadow: 0 0 15px rgba(102,252,241,0.3); }
    .lobby-btn { background: #45a29e; color: #0b0c10; width: 100%; padding: 15px; border: none; border-radius: 8px; font-size: 18px; font-weight: bold; cursor: pointer; text-transform: uppercase; transition: 0.3s; }
    .lobby-btn:hover { background: #66fcf1; transform: translateY(-3px); box-shadow: 0 10px 20px rgba(102,252,241,0.2); }

  
    .table-wood-rim { background: linear-gradient(to bottom, #3b2313, #1c1008); border-radius: 220px; padding: 35px; box-shadow: 0 30px 60px rgba(0,0,0,0.9), inset 0 10px 20px rgba(255,255,255,0.05); max-width: 1100px; margin: 40px auto; position: relative; }
    .table-felt { background: url('https://www.transparenttextures.com/patterns/felt.png'), radial-gradient(ellipse at center, #1b5e20 0%, #0a2e14 100%); border: 8px solid #111; border-radius: 180px; padding: 60px 40px; box-shadow: inset 0 0 80px rgba(0,0,0,0.9); display: flex; flex-direction: column; align-items: center; position: relative; }
    
    
    .card { background: linear-gradient(to bottom right, #ffffff, #f0f0f0); border-radius: 8px; width: 85px; height: 125px; box-shadow: 3px 5px 15px rgba(0,0,0,0.6); display: inline-flex; flex-direction: column; justify-content: space-between; padding: 5px; font-family: 'Georgia', serif; border: 1px solid #ccc; margin: 0 5px; transition: transform 0.2s; position: relative; }
    .card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; border: 1px solid rgba(255,255,255,0.5); border-radius: 7px; pointer-events: none; }
    .card:hover { transform: translateY(-15px) scale(1.05); z-index: 10; box-shadow: 5px 15px 25px rgba(0,0,0,0.7); }
    .card.red { color: #d32f2f; }
    .card.black { color: #212121; }
    .card-top { font-size: 20px; font-weight: bold; line-height: 1; text-align: left; }
    .card-center { font-size: 45px; text-align: center; flex-grow: 1; display: flex; align-items: center; justify-content: center; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); }
    .card-bottom { font-size: 20px; font-weight: bold; line-height: 1; text-align: right; transform: rotate(180deg); }

    
    .player-seat { background: linear-gradient(145deg, #2a2a2a, #1a1a1a); border: 2px solid #333; padding: 15px 25px; border-radius: 12px; text-align: center; min-width: 130px; box-shadow: 5px 5px 15px rgba(0,0,0,0.5); position: relative; }
    .player-seat::after { content: ''; position: absolute; top: 2px; left: 2px; right: 2px; bottom: 2px; border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; pointer-events: none; }
    .player-seat.active { border-color: #fbc02d; box-shadow: 0 0 25px rgba(251, 192, 45, 0.4); }
    .pot-display { font-size: 32px; font-weight: 900; color: #fbc02d; background: rgba(0,0,0,0.7); padding: 10px 30px; border-radius: 30px; border: 2px solid #555; text-shadow: 0 0 10px rgba(251, 192, 45, 0.5); box-shadow: 0 10px 20px rgba(0,0,0,0.6); margin-bottom: 30px; }
    
    .action-btn { color: white; padding: 15px 40px; border: none; border-radius: 30px; margin: 0 10px; cursor: pointer; font-weight: 900; font-size: 16px; letter-spacing: 1px; text-transform: uppercase; box-shadow: 0 5px 15px rgba(0,0,0,0.5); transition: 0.2s; }
    .btn-fold { background: linear-gradient(to bottom, #d32f2f, #b71c1c); }
    .btn-call { background: linear-gradient(to bottom, #757575, #424242); }
    .btn-raise { background: linear-gradient(to bottom, #388e3c, #1b5e20); }
    .action-btn:hover { transform: translateY(-3px); filter: brightness(1.2); }
    .action-btn:active { transform: translateY(2px); }

   
    #chat-panel { position: fixed; top: 0; right: -400px; width: 350px; height: 100%; background: #1f2833; border-left: 1px solid #45a29e; box-shadow: -10px 0 30px rgba(0,0,0,0.8); transition: right 0.3s cubic-bezier(0.4, 0.0, 0.2, 1); z-index: 1000; display: flex; flex-direction: column; }
    #chat-panel.open { right: 0; }
    .chat-header { background: #0b0c10; color: #66fcf1; padding: 20px; font-size: 18px; font-weight: bold; border-bottom: 1px solid #45a29e; display: flex; justify-content: space-between; align-items: center; }
    #chat-messages { flex-grow: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
    .chat-btn { position: fixed; bottom: 30px; right: 30px; background: #45a29e; color: #0b0c10; border: none; border-radius: 50px; padding: 15px 25px; font-size: 16px; font-weight: bold; cursor: pointer; box-shadow: 0 4px 15px rgba(69, 162, 158, 0.4); z-index: 1001; transition: 0.2s; }
    .chat-btn:hover { background: #66fcf1; }
    .msg-bot { background: rgba(211, 47, 47, 0.1); border-left: 4px solid #d32f2f; padding: 10px; border-radius: 4px; font-size: 14px; }
    .msg-player { background: rgba(102, 252, 241, 0.1); border-right: 4px solid #66fcf1; padding: 10px; border-radius: 4px; font-size: 14px; text-align: right; }
    .dealer-chip { 
    background: white; color: black; border-radius: 50%; 
    width: 35px; height: 35px; display: flex; 
    align-items: center; justify-content: center; 
    font-weight: bold; position: absolute; 
    top: 80px; right: 30%; border: 2px solid #555; 
    box-shadow: 0 4px 10px rgba(0,0,0,0.5); 
}                 
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
def post(session, nickname: str, room_choice: str): 
    session['nickname'] = nickname
    session['room_id'] = room_choice
    return RedirectResponse('/', status_code=303)

@rt('/')
def get(session):
    if 'nickname' not in session:
        return Html(
            Head(Title("Login | Casino"), casino_style),
            Body(
                Div(
                    Form(
    Input(type="text", name="nickname", placeholder="Твой ник...", required=True, cls="lobby-input"),
    Select(
        Option("💎 Las Vegas", value="Vegas"),
        Option("🏎️ Monaco", value="Monaco"),
        Option("🏮 Macau", value="Macau"),
        name="room_choice", cls="lobby-input"
    ),
    Button("JOIN TABLE", type="submit", cls="lobby-btn"),
    action="/login", method="post"
)
                    ),
                    cls="login-container"
            )
            )
        
    nickname = session['nickname']
    room = session.get('room_id', 'Lobby')
    room = session.get('room_id', 'Vegas')
    chat_script = Script("function toggleChat() { document.getElementById('chat-panel').classList.toggle('open'); }")
    visits = r.incr('visits')
    pot_key = f'hub:{hub_name}:game_state_v2'
    if not r.exists(pot_key):
        r.set(pot_key, 0)
    pot = r.get(pot_key)
    raw_hand = r.get('game_state_v2')
    if not raw_hand:
       new_hand = engine.deal_preflop([nickname])
       raw_hand = json.dumps(new_hand)
       r.set('game_state_v2', raw_hand)
    hand = json.loads(str(raw_hand))
    board_html = [PokerCard(c['rank'], c['suit'], c['color']) for c in hand['board']]
    my_cards_html = [PokerCard(c['rank'], c['suit'], c['color']) for c in hand['hands'].get(nickname, [])]
    fold_vals = json.dumps({"move": "fold", "player": nickname})
    call_vals = json.dumps({"move": "call", "player": nickname})
    raise_vals = json.dumps ({ "move": "raise", "player": nickname})
    return Html(
         Head(
            Title(f"{hub_name} Table"), 
            Script(src="https://unpkg.com/htmx.org@2.0.2"), 
            Script(src="https://unpkg.com/htmx-ext-ws@2.0.0/ws.js"),

            chat_script, 
            casino_style
        ),
        Body(
            
            BackgroundAnimations(),
            Div(
                H2(f"Welcome to {hub_name}", style="margin:0; color: #66fcf1; letter-spacing: 2px; text-transform: uppercase;"),
                P(f"Live Connections: {visits} | Server Health: Excellent", style="margin:5px 0 0 0; font-size: 12px; color: #c5c6c7;"),
                style="text-align: center; padding: 20px; background: rgba(11, 12, 16, 0.9); border-bottom: 2px solid #1f2833;"
            ),
            
            Div(
                Div(
                    Div(
                       Div(
    Div("D", cls="dealer-chip"), 
    Div(Div("Bot OOM-Killer", style="font-size: 12px; color: #aaa;"), Div("$1200", style="font-weight: bold; color: #fff;"), cls="player-seat"),
    Div(Div("SysAdmin", style="font-size: 12px; color: #aaa;"), Div("HOST", style="font-weight: bold; color: #fbc02d;"), cls="player-seat"),
    Div(Div("Toxic Senior", style="font-size: 12px; color: #aaa;"), Div("$850", style="font-weight: bold; color: #fff;"), cls="player-seat"),
    style="display: flex; justify-content: space-between; width: 100%; margin-bottom: 40px; position: relative;"
),
                        
                        Div(f"POT: ${pot}", id="pot-display", cls="pot-display"),
                        
                        Div(*board_html, id="board-cards", style="min-height: 130px; display: flex; justify-content: center; margin-bottom: 60px;"),
                        
                        Div(
                            Div(Div(f"👤 {nickname}", style="font-size: 12px; color: #aaa;"), Div("$1000", style="font-weight: bold; color: #fff;"), cls="player-seat active", style="margin: 0 auto 20px auto; width: fit-content;"),
                            Div(*my_cards_html, style="display: flex; justify-content: center; margin-bottom: 30px;"),
                            
                            Form(
                                Input(type="hidden", name="player", value=nickname),
                                Input(type="hidden", name="move", id="move-input", value=""),
                                Button("FOLD", type="submit", onclick="document.getElementById('move-input').value='fold'", cls="action-btn btn-fold"),
                                Button("CALL", type="submit", onclick="document.getElementById('move-input').value='call'", cls="action-btn btn-call"),
                                Button("RAISE", type="submit", onclick="document.getElementById('move-input').value='raise'", cls="action-btn btn-raise"),
                              
                                onsubmit="event.preventDefault();", ws_send=True, 
                                style="text-align: center;"
                            ),
                            style="width: 100%; text-align: center;"
                        ),
                        cls="table-felt"
                    ),
                    hx_ext="ws", ws_connect=f"/ws/hub/{hub_name}" 
                ),
                cls="table-wood-rim"
            ),
            Button(" Open Terminal", onclick="toggleChat()", cls="chat-btn"),
            Div(
                Div("Table Terminal", Span("✕", onclick="toggleChat()", style="cursor: pointer; color: #888;"), cls="chat-header"),
                Div(
                    Div(Div("SysAdmin:", style="color: #888; font-size: 11px;"), "Welcome to the cluster. Blinds are 10/20.", cls="msg-bot"),
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
        pot_key = f'hub:{hub_id}:game_state_v2'
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
if __name__ == '__main__':
    from fasthtml.common import serve
    serve(host='0.0.0.0', port=5001)