# -*- coding: utf-8 -*-
import os, sys, json, time, cmudict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXT  = os.path.join(ROOT, "extension")
DATA = os.path.join(ROOT, "data")

COST_THRESHOLD = 2.6

# residual: same-stress heteronyms machine can't cleanly separate from dialect variants
# (these need Phase-2 context / gemma). everything else auto-detected below.
RESIDUAL_HET = set("""read live use close lead bow tear wind bass sow row dove
wound minute house mouth excuse""".split())

def stress_idx(ph):
    """index (among vowels) of the primary-stressed vowel; -1 if none."""
    k = 0
    for p in ph:
        if engine.strip_stress(p) in engine.VOWELS_AR:
            if engine.stress_of(p) == 1:
                return k
            k += 1
    return -1

def is_heteronym(prons):
    """machine rule: TRUE heteronym if primary stress falls on different syllables."""
    idxs = {stress_idx(p) for p in prons}
    return len(idxs) > 1

d = cmudict.dict()
words = {}
outliers = []
heteronyms = []
t0 = time.time()

for w, prons in d.items():
    if not w.isalpha():
        continue
    wl = w.lower()
    if len(prons) > 1:
        if is_heteronym(prons):                       # auto-detected stress-shift
            outliers.append([wl, "heteronym"]); heteronyms.append([wl, "stress-shift"]); continue
        if wl in RESIDUAL_HET:                         # known same-stress heteronym
            outliers.append([wl, "heteronym"]); heteronyms.append([wl, "vowel-residual"]); continue
        # else: weak/strong or dialect variant -> render from primary pron
    ph = prons[0]
    try:
        full, cost = engine.render(wl, ph, full=True)
        adv,  _    = engine.render(wl, ph, full=False)
    except Exception:
        outliers.append([wl, "err"]); continue
    if full is None or cost > COST_THRESHOLD:
        outliers.append([wl, "lowconf"]); continue
    if full != wl or adv != wl:
        words[wl] = {"f": full, "a": adv}

dt = time.time() - t0

base = {"version": engine.RULE_VERSION, "n": len(words), "words": words}
json.dump(base, open(os.path.join(EXT,"base-dict.json"),"w",encoding="utf-8"), ensure_ascii=False)
json.dump({"version": engine.RULE_VERSION, "outliers": outliers},
          open(os.path.join(DATA,"outliers.json"),"w",encoding="utf-8"), ensure_ascii=False)
json.dump({"version": engine.RULE_VERSION, "n": len(heteronyms), "heteronyms": heteronyms},
          open(os.path.join(DATA,"heteronyms.json"),"w",encoding="utf-8"), ensure_ascii=False)
n_shift = sum(1 for h in heteronyms if h[1]=="stress-shift")
print(f"built in {dt:.1f}s")
print(f"rendered (with marks): {len(words)}")
print(f"outliers (bare):       {len(outliers)}")
print(f"heteronyms auto-detected: {len(heteronyms)}  (stress-shift {n_shift}, residual {len(heteronyms)-n_shift})")
