import random
from collections import Counter
from itertools import combinations

SUITS = ['♠', '♥', '♦', '♣']
RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
RANK_VALUES = {r: i + 2 for i, r in enumerate(RANKS)}

BOT_NAMES = ['Toxic Senior', 'OOM-Killer']

TOXIC_FOLD = ["Toxic Senior: Fold? I've seen failed pipelines with more courage. 🐔", "Toxic Senior: 404 Courage Not Found."]
TOXIC_RAISE = ["Toxic Senior: Raising? Bold move for someone who pushes to main without tests. 🚀", "Toxic Senior: I bet your Dockerfile has a critical CVE."]
TOXIC_CALL = ["Toxic Senior: Boring call. LGTM, moving on.", "Toxic Senior: Approved. Merging your bet into the pot."]

OOM_CALL = ["OOM-Killer: Allocating patience... I call.", "OOM-Killer: Garbage collection paused. Let's see your cards."]
OOM_FOLD = ["OOM-Killer: Segfault. Retreating from this hand.", "OOM-Killer: Process terminated. Hand garbage collected."]
OOM_RAISE = ["OOM-Killer: Stack overflow! Raising the limit! ", "OOM-Killer: Heap expansion initiated. I raise."]
HAND_NAMES = {
    8: "Straight Flush",
    7: "Four of a Kind",
    6: "Full House",
    5: "Flush",
    4: "Straight",
    3: "Three of a Kind",
    2: "Two Pair",
    1: "Pair",
    0: "High Card",
}
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
        'dealer_log': ['🃏 Dealer: Cards have been dealt. Preflop begins!'],
    }
def deal_next_phase(game_state):
    deck = game_state['deck']
    board = game_state['board']
    phase = game_state['phase']
    log = game_state.get('dealer_log', [])

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
        log.append('🃏 Dealer: SHOWDOWN!')

    game_state['deck'] = deck
    game_state['board'] = board
    game_state['dealer_log'] = log[-10:]
    return game_state
def straight_high(values):
    vals = set(values)

    for high in range(14, 5, -1):
        if all(v in vals for v in range(high - 4, high + 1)):
            return high

    if {14, 5, 4, 3, 2}.issubset(vals):
        return 5

    return None
def evaluate_5(cards):
    values = sorted([RANK_VALUES[c['rank']] for c in cards], reverse=True)
    suits = [c['suit'] for c in cards]
    counts = Counter(values)
    flush = len(set(suits)) == 1
    straight = straight_high(values)

    if flush and straight:
        return (8, [straight])

    quads = [v for v, c in counts.items() if c == 4]
    if quads:
        q = max(quads)
        kicker = max(v for v in values if v != q)
        return (7, [q, kicker])

    trips = sorted([v for v, c in counts.items() if c == 3], reverse=True)
    pairs = sorted([v for v, c in counts.items() if c == 2], reverse=True)

    if trips and (pairs or len(trips) > 1):
        return (6, [trips[0], trips[1] if len(trips) > 1 else pairs[0]])
    if flush:
        return (5, values)
    if straight:
        return (4, [straight])
    if trips:
        kickers = [v for v in values if v != trips[0]][:2]
        return (3, [trips[0]] + kickers)
    if len(pairs) >= 2:
        kicker = max(v for v in values if v not in pairs[:2])
        return (2, pairs[:2] + [kicker])
    if len(pairs) == 1:
        kickers = [v for v in values if v != pairs[0]][:3]
        return (1, [pairs[0]] + kickers)

    return (0, values)


def best_hand(cards):
    if len(cards) < 5:
     return (0, [])
    return max(evaluate_5(list(combo)) for combo in combinations(cards, 5))
def hand_name(score):
    return HAND_NAMES.get(score[0], "High Card")
def preflop_strength(hole_cards):
    r1 = RANK_VALUES[hole_cards[0]['rank']]
    r2 = RANK_VALUES[hole_cards[1]['rank']]
    score = (r1 + r2) / 28.0
    if r1 == r2:
        score += 0.25
    if hole_cards[0]['suit'] == hole_cards[1]['suit']:
        score += 0.06
    if abs(r1 - r2) <= 2:
        score += 0.04

    return min(score, 1.0)
def postflop_strength(hole_cards, board_cards):
    score = best_hand(hole_cards + board_cards)
    return min(1.0, score[0] / 8.0 + sum(score[1][:2]) / 100.0)
def bot_decide_move(bot_name, bot_cards, board_cards, current_pot, current_bet):
    if not bot_cards:
        return {"move": "fold", "phrase": f"{bot_name}: No cards — folding."}
    strength = postflop_strength(bot_cards, board_cards) if board_cards else preflop_strength(bot_cards)
    rand = random.random()
    if current_bet == 0 and strength < 0.18:
        return {"move": "call", "phrase": f"{bot_name}: I check."}
    if bot_name == 'Toxic Senior':
        if strength < 0.28 and rand < 0.55:
            return {"move": "fold", "phrase": random.choice(TOXIC_FOLD)}
        if strength > 0.62 and rand < 0.55:
            return {"move": "raise", "phrase": random.choice(TOXIC_RAISE)}
        return {"move": "call", "phrase": random.choice(TOXIC_CALL)}
    if strength < 0.22 and rand < 0.45:
        return {"move": "fold", "phrase": random.choice(OOM_FOLD)}
    if strength > 0.68 or current_pot > 600:
        return {"move": "raise", "phrase": random.choice(OOM_RAISE)}
    return {"move": "call", "phrase": random.choice(OOM_CALL)}
