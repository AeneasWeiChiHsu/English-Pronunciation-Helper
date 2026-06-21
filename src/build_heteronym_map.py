# -*- coding: utf-8 -*-
"""
Build data/heteronym-map.json : for each heteronym, list its CMUdict
pronunciations with stress position + rendered forms, so render.py can
pick the right one once a POS / sense is known.

Stress-shift rule (classic English N/V pairs): noun/adj -> earlier primary
stress, verb -> later primary stress. Vowel-residual ones (read/live/use...)
are tagged for sense-based resolution (handled in render.py).
"""
import os, sys, json, cmudict
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import engine
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

VOWELS = engine.VOWELS_AR
def stress_idx(ph):
    k = 0
    for p in ph:
        if engine.strip_stress(p) in VOWELS:
            if engine.stress_of(p) == 1: return k
            k += 1
    return -1

# the 13 same-stress vowel heteronyms need sense, not POS
RESIDUAL = set("""read live use close lead bow tear wind bass sow row dove
wound minute house mouth excuse""".split())

d = cmudict.dict()
het = [h[0] for h in json.load(open(os.path.join(DATA, "heteronyms.json")))["heteronyms"]]

out = {}
for w in het:
    prons = d.get(w)
    if not prons:
        continue
    variants = []
    seen = set()
    for ph in prons:
        full, cost = engine.render(w, ph, full=True)
        adv,  _    = engine.render(w, ph, full=False)
        key = (full, adv)
        if key in seen:
            continue
        seen.add(key)
        variants.append({"stress_idx": stress_idx(ph), "pron": ph, "f": full, "a": adv})
    if len(variants) < 2:
        continue
    variants.sort(key=lambda v: v["stress_idx"])
    if w in RESIDUAL:
        out[w] = {"type": "vowel-residual", "variants": variants}
    else:
        # stress-shift: index 0 = earliest stress (noun/adj), last = latest (verb)
        out[w] = {
            "type": "stress-shift",
            "variants": variants,
            "pos_default": {"NOUN": 0, "PROPN": 0, "ADJ": 0, "VERB": len(variants) - 1},
        }

json.dump({"version": engine.RULE_VERSION, "n": len(out), "map": out},
          open(os.path.join(DATA, "heteronym-map.json"), "w", encoding="utf-8"),
          ensure_ascii=False)
print("heteronym-map built:", len(out), "entries")
print("sample record:", json.dumps(out.get("record"), ensure_ascii=False))
print("sample read:  ", json.dumps(out.get("read"), ensure_ascii=False))
