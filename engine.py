import random
from collections import Counter
SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i for i, r in enumerate(RANKS)}
BOT_NAMES = ['Toxic Senior', 'OOM-Killer']
TOXIC_FOLD  = ["Toxic Senior: Fold? I've seen failed pipelines with more courage. 🐔",
               "Toxic Senior: 404 Courage Not Found.", "Toxic Senior: You fold faster than a cheap CI runner."]
TOXIC_RAISE = ["Toxic Senior: Raising? Bold move for someone who pushes to main without tests. 🚀",
               "Toxic Senior: I bet your Dockerfile has a critical CVE. I CALL."]
TOXIC_CALL  = ["Toxic Senior: Boring call. LGTM, moving on.",
               "Toxic Senior: Approved. Merging your bet into the pot."]
OOM_ALLIN   = ["OOM-Killer: FATAL ERROR. MEMORY LIMIT EXCEEDED. ALL-IN! 🛑",
               "OOM-Killer: Kernel panic! Dumping ALL MY CHIPS!"]
OOM_CALL    = ["OOM-Killer: Allocating 50MB of patience... I call.",
               "OOM-Killer: Garbage collection paused. Let's see your cards."]
OOM_FOLD    = ["OOM-Killer: Segfault. Retreating from this hand.",
               "OOM-Killer: Process terminated. Hand garbage collected."]
OOM_RAISE   = ["OOM-Killer: Stack overflow! Raising the limit! 🔥",
               "OOM-Killer: Heap expansion initiated. I raise."]
def get_color(suit):
    return "red" if suit in ['♥', '♦'] else "black"
def create_deck():
    deck = [{'rank': r, 'suit': s, 'color': get_color(s)} for s in SUITS for r in RANKS]
    random.shuffle(deck)
    return deck
def deal_preflop(live_player_names):
    deck = create_deck()
    hands = {}
    for name in live_player_names:
        hands[name] = [deck.pop(), deck.pop()]
    for bot in BOT_NAMES:
        hands[bot] = [deck.pop(), deck.pop()]
    return {
        'hands': hands,
        'board': [],
        'deck': deck,
        'phase': 'preflop',
        'bot_folded': {b: False for b in BOT_NAMES},
        'dealer_log': ['🃏 Dealer: Cards have been dealt. Preflop begins!'],
    }
def deal_next_phase(game_state):
    deck  = game_state['deck']
    board = game_state['board']
    phase = game_state['phase']
    log   = game_state.get('dealer_log', [])
    if phase == 'preflop':
        board.extend([deck.pop(), deck.pop(), deck.pop()])
        game_state['phase'] = 'flop'
        log.append('🃏 Dealer: Flop — 3 community cards revealed.')
    elif phase == 'flop':
        board.append(deck.pop())
        game_state['phase'] = 'turn'
        log.append('🃏 Dealer: Turn card revealed.')
    elif phase == 'turn':
        board.append(deck.pop())
        game_state['phase'] = 'river'
        log.append('🃏 Dealer: River — final card. Last round!')
    elif phase == 'river':
        game_state['phase'] = 'showdown'
        log.append('🃏 Dealer: SHOWDOWN! Best hand wins.')
    game_state['deck']       = deck
    game_state['board']      = board
    game_state['dealer_log'] = log[-10:]
    return game_state
def evaluate_hand_strength(hole_cards, board_cards):
    all_cards   = hole_cards + board_cards
    ranks       = [RANK_VALUES[c['rank']] for c in all_cards]
    suits       = [c['suit'] for c in all_cards]
    rank_counts = Counter(ranks)
    suit_counts = Counter(suits)
    counts      = sorted(rank_counts.values(), reverse=True)
    is_flush    = any(v >= 5 for v in suit_counts.values())
    sr          = sorted(set(ranks))
    is_straight = any(sr[i+4]-sr[i]==4 and len(sr[i:i+5])==5 for i in range(len(sr)-4))
    if is_straight and is_flush: return 8
    if counts[0] == 4: return 7
    if counts[0] == 3 and len(counts) > 1 and counts[1] == 2: return 6
    if is_flush: return 5
    if is_straight: return 4
    if counts[0] == 3: return 3
    if counts[0] == 2 and len(counts) > 1 and counts[1] == 2: return 2
    if counts[0] == 2: return 1
    return 0
def preflop_strength(hole_cards):
    r1 = RANK_VALUES[hole_cards[0]['rank']]
    r2 = RANK_VALUES[hole_cards[1]['rank']]
    score = (max(r1,r2) + min(r1,r2)) / 26.0
    if r1 == r2: score += 0.2
    if hole_cards[0]['suit'] == hole_cards[1]['suit']: score += 0.05
    return min(score, 1.0)
def bot_decide_move(bot_name, bot_cards, board_cards, current_pot, current_bet):
    if not bot_cards:
        return {"move": "fold", "phrase": f"{bot_name}: No cards — folding."}
    strength = (evaluate_hand_strength(bot_cards, board_cards) / 8.0
                if board_cards else preflop_strength(bot_cards))
    rand = random.random()
    if bot_name == 'Toxic Senior':
        if strength < 0.25 and rand < 0.6:
            return {"move": "fold",  "phrase": random.choice(TOXIC_FOLD)}
        if strength > 0.6 and rand < 0.5:
            return {"move": "raise", "phrase": random.choice(TOXIC_RAISE)}
        return {"move": "call", "phrase": random.choice(TOXIC_CALL)}
    else:
        if current_pot > 500 or strength > 0.75:
            return {"move": "raise", "phrase": random.choice(OOM_ALLIN)}
        if strength < 0.2 and rand < 0.4:
            return {"move": "fold",  "phrase": random.choice(OOM_FOLD)}
        return {"move": "call", "phrase": random.choice(OOM_CALL)}
 