
def analyze_syntax_modifiers(token, doc, config):
    """Analizuje drzewo zależności i sąsiedztwo tokena."""
    is_negated = False
    neg_triggers = config["negation_triggers"]
    adv_modifiers = config["adverb_modifiers"]
    intensifiers = config["intensifiers"]

    # 1. Negacja
    for child in token.children:
        if child.lower_ in neg_triggers:
            is_negated = True
            break
    if not is_negated and token.head.text.lower() in neg_triggers:
        is_negated = True
    if not is_negated and token.head.pos_ in ["VERB", "AUX"]:
        for child in token.head.children:
            if child.lower_ in neg_triggers:
                is_negated = True
                break
    if is_negated:
        return -10000.0, ["NEGACJA"]

    # 2. Modyfikatory (Linear Lookback logic)
    modifier_sum = 0.0
    found_mods = []
    processed_indices = set()
    candidates = []

    # A. Z drzewa
    for child in token.children:
        if child.text.lower() in adv_modifiers:
            candidates.append(child)
            processed_indices.add(child.i)

    # B. Liniowo wstecz
    cursor = token.i - 1
    steps = 0
    while cursor >= 0 and steps < 4:
        neighbor = doc[cursor]
        steps += 1
        if neighbor.is_punct or neighbor.is_space:
            cursor -= 1
            continue
        if neighbor.text.lower() in adv_modifiers:
            if neighbor.i not in processed_indices:
                candidates.append(neighbor)
                processed_indices.add(neighbor.i)
                break
            else:
                break
        else:
            break
        cursor -= 1

    # 3. Obliczanie
    for mod_token in candidates:
        word = mod_token.text.lower()
        base_val = adv_modifiers.get(word, 0)
        current_mod_impact = base_val
        mod_desc = f"{word}({base_val})"

        for grandchild in mod_token.children:
            gc_word = grandchild.text.lower()
            if gc_word in intensifiers:
                if base_val < 0:
                    current_mod_impact += -0.2
                    mod_desc += f" + {gc_word}(deep-neg)"
                else:
                    current_mod_impact += 0.2
                    mod_desc += f" + {gc_word}(deep-pos)"

        modifier_sum += current_mod_impact
        found_mods.append(mod_desc)

    return (modifier_sum, found_mods) if found_mods else (0.0, [])


def translate_batch(words, tokenizer, model):
    """Wrapper na tłumaczenie."""
    if not words or not model or not tokenizer: return []
    encoded = tokenizer(words, return_tensors="pt", padding=True)
    translated = model.generate(**encoded, num_beams=1, do_sample=False, max_new_tokens=10)
    return [tokenizer.decode(t, skip_special_tokens=True) for t in translated]


def calculate_stars(weights):
    """
    Przelicza wagi na gwiazdki (1-7).
    Obsługuje również twarde wykluczenia (ocena -1).
    """
    if not weights:
        return 0

    has_positive = any(w > 0 for w in weights)
    has_negative = any(w < 0 for w in weights)
    if has_positive and has_negative:
        return 0
    if has_negative and not has_positive:
        return -1

    raw_sum = sum(weights)
    bonus = (len(weights) - 1) * 0.1
    total = max(0.0, min(1.0, raw_sum + bonus))
    return min(7, int(1 + (total * 6)))