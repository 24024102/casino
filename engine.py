import random 
import json
from collections import Counter
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
    "Toxic Senior: Boring call. LGTM, moving on. ",
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
        'phase': 'preflop',
        'bot_folded': {'Toxic Senior': False, 'OOM-Killer': False},  
        'dealer_log': ["Dealer: Cards have been dealt. Preflop begins!"]  

    }
def deal_next_phase(game_state):
    deck = game_state['deck']
    board = game_state['board']
    phase = game_state['phase']
    log = game_state.get('dealer_log', [])
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
def evaluate_hand_strength(hole_cards,board_cards):
    all_cards = hole_cards + board_cards
    ranks = [RANK_VALUES[c['rank']] for c in all_cards]
    suits = [c['suit'] for c in all_cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    counts = sorted(rank_counts.values(), reverse=True)
    is_flush = any(v >=5 for v in suit_counts.values())
    sorted_ranks = sorted(set(ranks))
    is_straight = any(
        sorted_ranks[i+4] - sorted_ranks[i] == 4 and len(sorted_ranks[i:i+5]) == 5
        for i in range(len(sorted_ranks) - 4)
    )

    if is_straight and is_flush:
        return 8 #straight flush
    if counts[0] == 4:
        return 7 
    if counts[0] == 3 and counts == 2:
        return 6
    if is_flush:
        return 5
    if is_straight:
        return 4
    if counts[0] == 3:
        return 3
    if counts[0] == 2 and counts[1] == 2:
        return 2
    if counts[0] == 2:
        return 1
    return 0

def preflop_strength(hole_cards):
    r1 = RANK_VALUES[hole_cards[0]['rank']]
    r2 = RANK_VALUES[hole_cards[0]['rank']]
    suited = hole_cards[0]['suit'] == hole_cards[1]['suit']
    high = max(r1, r2)
    low = min(r1, r2)
    score = (high + low) / 26.0
    if r1 == r2:
        score += 0.2
    if suited:
        score += 0.05
    return min(score, 1.0)

def bot_decide_move(bot_name, bot_cards, board_cards, current_pot, current_bet):
    if board_cards:
        strength = evaluate_hand_strength(bot_cards, board_cards) / 8.0
    else:
        strength = preflop_strength(bot_cards)

    
    rand = random.random()

    if bot_name == "Toxic Senior":
        
        if strength < 0.25 and rand < 0.6:
            move = "fold"
            phrase = random.choice(TOXIC_FOLD_RESPONSE)
        elif strength > 0.6 and rand < 0.5:
            move = "raise"
            phrase = random.choice(TOXIC_RAISE)
        else:
            move = "call"
            phrase = random.choice(TOXIC_CALL)
    else:
      
        if current_pot > 500 or strength > 0.75:
            move = "raise"
            phrase = random.choice(OOM_ALLIN)
        elif strength < 0.2 and rand < 0.4:
            move = "fold"
            phrase = random.choice(OOM_FOLD_PHRASES)
        else:
            move = "call"
            phrase = random.choice(OOM_CALL_PHRASES if current_pot <= 500 else OOM_RAISE_PHRASES)

    return {"move": move, "phrase": phrase}
