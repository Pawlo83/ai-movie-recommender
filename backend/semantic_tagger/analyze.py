from langdetect import detect, LangDetectException
from sentence_transformers import util

from .lang_configs import LANG_CONFIGS, BLOCKED_TAGS
from .resources import RESOURCES, initialize_tagger, get_spacy_model
from .logic import analyze_syntax_modifiers, translate_batch, calculate_stars


def analyze_text(text):
    """Główny punkt wejścia dla analizy semantycznej tekstu."""
    tag_hits = extract_raw_concepts(text)
    mapped_tags = map_tags_to_db(tag_hits)
    return mapped_tags

def extract_raw_concepts(text):
    """
    Silnik NLP bazujący na SpaCy.
    
    Funkcja:
    - oczyszcza tekst z interpunkcji i tzw. stop-words,
    - wyłapuje kluczowe części mowy,
    - rozpoznaje kontekst sąsiednich słów,
    - wykrywa i obsługuje twarde negacje (np. "nie chcę", "bez").
    """
    if not RESOURCES["is_initialized"]:
        initialize_tagger()

    detected_lang = 'en'

    config = LANG_CONFIGS[detected_lang]
    nlp = get_spacy_model(config["model_name"])

    doc = nlp(text)

    with doc.retokenize() as retokenizer:
            start = None
            for i, token in enumerate(doc):
                if token.pos_ in ["PROPN", "NOUN"]:
                    if start is None:
                        start = i
                else:
                    if start is not None and (i - start) > 1:
                        retokenizer.merge(doc[start:i])
                    start = None
            if start is not None and (len(doc) - start) > 1:
                retokenizer.merge(doc[start:len(doc)])

    candidates_data = []
    PRESENCE_BONUS = 0.40

    for token in doc:
        if token.is_punct or token.is_space or token.like_num or token.is_stop: continue
        if token.pos_ not in ["NOUN", "ADJ", "VERB", "PROPN"]: continue

        lemma = token.lemma_.lower()
        mod_value, mod_text_list = analyze_syntax_modifiers(token, doc, config)

        if mod_value <= -1000:
            is_negated = True
            final_weight = 0
        else:
            is_negated = False
            final_weight = max(0.0, PRESENCE_BONUS + mod_value)

        candidates_data.append({
            "lemma": lemma, "weight": final_weight, "is_negated": is_negated
        })

    if not candidates_data: return {}, set()

    lemmas_translated = [x["lemma"] for x in candidates_data]

    tag_hits = {}

    for i, original in enumerate(candidates_data):
        en_word = lemmas_translated[i].lower().replace(".", "").strip()
        if en_word.startswith("the ") and len(en_word) > 4: en_word = en_word[4:]
        if en_word not in tag_hits: tag_hits[en_word] = []

        if original["is_negated"]:
            tag_hits[en_word].append(-1.0)
        else:
            tag_hits[en_word].append(original["weight"])

    return tag_hits

def map_tags_to_db(tag_hits):
    """
    Wykorzystuje model SentenceTransformers do znalezienia matematycznego podobieństwa 
    między surowymi tagami/słowami a oficjalną listą tagów z bazy danych.
    """
    if not RESOURCES["is_initialized"]:
        initialize_tagger()

    if not tag_hits:
        return []
        
    final_criterions = []
    tags_to_process = []
    is_list = isinstance(tag_hits, list)

    if is_list:
        converted_dict = {}
        for item in tag_hits:
            t = item.get("tag", "").lower()
            if t:
                if t not in converted_dict:
                    converted_dict[t] = []
                converted_dict[t].append(item.get("rating", 0))
        tag_hits = converted_dict
    tags_to_process = list(tag_hits.keys())

    if not tags_to_process:
        return []

    sim_model = RESOURCES["similarity_model"]
    db_vectors = RESOURCES["db_vectors"]
    db_tags_list = RESOURCES["db_tags_list"]

    if db_vectors is not None and tags_to_process:
        cand_vectors = sim_model.encode(tags_to_process, convert_to_tensor=True)
        cos_scores = util.cos_sim(cand_vectors, db_vectors)
        aggregated_hits = {}

        for i, cand_word in enumerate(tags_to_process):
            scores = cos_scores[i]
            best_idx = scores.argmax().item()
            best_score = scores[best_idx].item()
            found_db_tag = db_tags_list[best_idx]

            if found_db_tag in BLOCKED_TAGS: continue

            if best_score >= 0.75:
                if found_db_tag not in aggregated_hits: aggregated_hits[found_db_tag] = []
                aggregated_hits[found_db_tag].extend(tag_hits[cand_word])

        for tag, weights in aggregated_hits.items():
            if is_list:
                stars = max(weights)
            else:
                stars = calculate_stars(weights)

            if stars != 0:
                final_criterions.append({"tag": tag, "rating": stars})

    final_criterions.sort(key=lambda x: x['rating'], reverse=True)
    return final_criterions