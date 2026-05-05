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
def deal_new_round():
    deck = [{'rank': r, 'suit': s,'color': get_color(s) } for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return {
        'player': [deck.pop(), deck.pop()],
        'bot_oom': [deck.pop(), deck.pop()],
        'bot_toxic': [deck.pop(), deck.pop()],
        'board': [deck.pop(), deck.pop(), deck.pop(), deck.pop()],
        'deck_left': len(deck)


    }
def get_bot_reaction(bot_name, player_move, current_pot):
    if bot_name == "Toxic Senior":
        if player_move == "fold": return random.choice(TOXIC_FOLD)
        elif player_move == "raise": return random.choice(TOXIC_RAISE)
        else: return random.choice(TOXIC_CALL)
            
    elif bot_name == "Bot OOM-Killer":
        if current_pot > 500: return random.choice(OOM_ALLIN)
        else: return random.choice(OOM_CALL_PHRASES)