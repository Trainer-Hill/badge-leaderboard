import th_helpers.components.deck_label

def create_label(deck):
    if not deck:
        return None
    deck['icons'] = [i if i.startswith('https') else th_helpers.components.deck_label.get_pokemon_icon(i) for i in deck.get('icons', [])]
    return th_helpers.components.deck_label.format_label(deck)
