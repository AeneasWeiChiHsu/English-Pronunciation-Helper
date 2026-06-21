# -*- coding: utf-8 -*-
"""Resolve heteronyms to a single pronunciation variant.

Layer 1 (no LLM): spaCy POS tagging. For stress-shift heteronyms a clean
NOUN/VERB/ADJ tag picks the variant directly -> most cases never hit gemma.

Layer 2 (gemma via Ollama): only the leftovers --
  - stress-shift where spaCy POS was unhelpful
  - the 13 vowel-residual heteronyms (need tense/sense, not just POS)
Calls are collected and run in one pass (model stays warm). format:json.
"""
from ollama_client import ask_json, is_up, MODEL

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm", disable=["ner", "lemmatizer"])
except Exception:
    _NLP = None

# vowel-residual: gemma question + map(answer -> phoneme that must appear in chosen pron)
RESIDUAL_Q = {
    "read":  ("Is '{w}' past tense or present tense here? Answer 'past' or 'present'.",
              {"past": "EH", "present": "IY"}),
    "lead":  ("Does '{w}' mean the metal, or to guide/be first? Answer 'metal' or 'guide'.",
              {"metal": "EH", "guide": "IY"}),
    "live":  ("Is '{w}' a verb (to be alive) or an adjective (broadcast live)? Answer 'verb' or 'adjective'.",
              {"verb": "IH", "adjective": "AY"}),
    "use":   ("Is '{w}' a noun or a verb here? Answer 'noun' or 'verb'.",
              {"noun": "S", "verb": "Z"}),
    "close": ("Is '{w}' an adjective/adverb (near) or a verb (to shut)? Answer 'near' or 'shut'.",
              {"near": "S", "shut": "Z"}),
    "wind":  ("Does '{w}' mean moving air (noun) or to twist/turn (verb)? Answer 'air' or 'twist'.",
              {"air": "IH", "twist": "AY"}),
    "tear":  ("Does '{w}' mean a teardrop or to rip? Answer 'drop' or 'rip'.",
              {"drop": "IH", "rip": "EH"}),
    "bow":   ("Does '{w}' mean a knot/weapon (rhymes with 'go') or to bend (rhymes with 'now')? Answer 'go' or 'now'.",
              {"go": "OW", "now": "AW"}),
    "wound": ("Does '{w}' mean an injury, or is it the past tense of 'wind'? Answer 'injury' or 'wound-up'.",
              {"injury": "UW", "wound-up": "AW"}),
    "sow":   ("Does '{w}' mean to plant seeds (rhymes 'go') or a female pig (rhymes 'now')? Answer 'plant' or 'pig'.",
              {"plant": "OW", "pig": "AW"}),
}

def _spacy_pos(sentences):
    """Return {(sent_id, offset_in_sentence): POS}."""
    pos = {}
    if _NLP is None:
        return pos
    for s in sentences:
        doc = _NLP(s["text"])
        for tok in doc:
            pos[(s["sent_id"], tok.idx)] = tok.pos_
    return pos

def _pick_by_phoneme(variants, sig):
    for i, v in enumerate(variants):
        if any(sig in p for p in v["pron"]):
            return i
    return 0

def disambiguate(gated, sentences, use_gemma=True):
    sent_by_id = {s["sent_id"]: s for s in sentences}
    pos_map = _spacy_pos(sentences)
    report = {"spacy": 0, "gemma": 0, "fallback": 0, "decisions": []}
    gemma_ok = use_gemma and is_up()

    for g in gated:
        if g.get("action") != "heteronym":
            continue
        w = g["text"]; lw = w.lower().strip("'")
        het = g["het"]; variants = het["variants"]
        chosen, who = None, None

        # ---- Layer 1: spaCy POS (stress-shift only) ----
        if het["type"] == "stress-shift":
            off = g["start"] - sent_by_id[g["sent_id"]]["start"]
            pos = pos_map.get((g["sent_id"], off))
            idx = het["pos_default"].get(pos) if pos else None
            if idx is not None:
                chosen, who = idx, "spacy"

        # ---- Layer 2: gemma (leftovers + all residual) ----
        if chosen is None and gemma_ok:
            sent = sent_by_id[g["sent_id"]]["text"].strip()
            if het["type"] == "vowel-residual" and lw in RESIDUAL_Q:
                q, amap = RESIDUAL_Q[lw]
                prompt = (f'Sentence: "{sent}"\n{q.format(w=w)}\n'
                          f'Reply as JSON: {{"answer": "..."}}')
                ans = ask_json(prompt).get("answer", "").lower()
                sig = next((amap[k] for k in amap if k in ans), None)
                if sig:
                    chosen, who = _pick_by_phoneme(variants, sig), "gemma"
            else:  # stress-shift fallback
                prompt = (f'Sentence: "{sent}"\n'
                          f"Is '{w}' a noun or a verb here?\n"
                          f'Reply as JSON: {{"pos": "noun"|"verb"}}')
                pos = ask_json(prompt).get("pos", "").lower()
                if pos in ("noun", "verb"):
                    chosen = 0 if pos == "noun" else len(variants) - 1
                    who = "gemma"

        # ---- fallback: leave bare ----
        if chosen is None:
            g["action"] = "bare"; report["fallback"] += 1
            report["decisions"].append({"word": w, "by": "fallback->bare"})
            continue

        v = variants[chosen]
        marked = v["a"]
        if w[:1].isupper() and marked[:1].islower():
            marked = marked[0].upper() + marked[1:]
        g["action"] = "render"; g["marked"] = marked if marked != lw else None
        if g["marked"] is None:
            g["action"] = "bare"
        report[who] += 1
        report["decisions"].append({"word": w, "by": who, "pick": v["f"]})
    return report
