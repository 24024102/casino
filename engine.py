import random 
import json
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']


TOXIC_FOLD = [
    "Toxic Senior: Fold? I've seen failed pipelines with more courage. 🐔",
    "Toxic Senior: 404 Courage Not Found. Go read the documentation.",
    "Toxic Senior: You fold faster than a cheap CI runner.",
    "Toxic Senior: Good choice. Your hand was as weak as your last pull request."
]
TOXIC_RAISE = [
    "Toxic Senior: Raising? Bold move for someone who pushes to main without testing. I CALL. 🚀",
    "Toxic Senior: Oh, so we are doing load testing now? Bring it on.",
    "Toxic Senior: I bet you don't even know your Dockerfile has a critical vulnerability. I CALL."
]
TOXIC_CALL = [
    "Toxic Senior: Boring call. LGTM, moving on. 🥱",
    "Toxic Senior: Just a call? You lack the vision for architecture.",
    "Toxic Senior: Approved. Merging your bet into the pot."
]

OOM_ALLIN = [
    "Bot OOM-Killer: FATAL ERROR. MEMORY LIMIT EXCEEDED. I'M GOING ALL-IN! 🛑",
    "Bot OOM-Killer: Kernel panic! Dumping core and ALL MY CHIPS into the pot!",
    "Bot OOM-Killer: SIGKILL activated. Say goodbye to your balance."
]
OOM_CALL_PHRASES = [
    "Bot OOM-Killer: Allocating 50MB of patience... I call.",
    "Bot OOM-Killer: Garbage collection paused. Let's see your cards.",
    "Bot OOM-Killer: I have 99 processes and this bet ain't one. Call."
]
def get_color(suit):
    return "red" if suit in [ '♥', '♦'] else "black"
def create_deck():
    deck = [{'rank': r, 'suit': s, 'color': get_color(s)} for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck
def deal_preflop(live_player_names):
    deck = create_deck()
    hands = {}
    for name in live_player_names:
        hands[name] = [deck.pop(), deck.pop()]
    hands['bot_oom'] = [deck.pop(), deck.pop()]
    hands['toxic_senior'] =  [deck.pop(), deck.pop()]
    return {
        'hands': hands,
        'board': [],
        'deck': deck,
        'phase': 'preflop'
    }
def deal_next_phase(game_state):
    deck = game_state['deck']
    board = game_state['board']
    phase = game_state['phase']
    if phase == 'preflop':
        board.extend([deck.pop(), deck.pop(), deck.pop()])
        game_state['phase'] = 'flop' 
    elif phase == 'flop':
        board.append(deck.pop())
        game_state['phase'] = 'turn'
    elif phase == 'turn':
        board.append(deck.pop())
        game_state['phase'] = 'river'
    game_state['deck'] = deck
    game_state['board'] = board
    return game_state
def bot_decide_move(bot_name, bot_cards, board_cards, current_pot, current_bet):
    """
    В будущем бот будет смотреть на свои карты и решать: Фолд, Колл или Рейз.
    Пока что они всегда делают CALL (чтобы игра не ломалась), но говорят твои крутые фразы.
    """
    # ... здесь будет математика покера ...
    
    move = "call" 
    
    # Выбираем фразу
    if bot_name == "Toxic Senior":
        phrase = random.choice(TOXIC_CALL)
    else:
        phrase = random.choice(OOM_ALLIN) if current_pot > 500 else random.choice(OOM_CALL_PHRASES)
        
    return {"move": move, "phrase": phrase}