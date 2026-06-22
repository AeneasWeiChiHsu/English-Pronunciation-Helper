# -*- coding: utf-8 -*-
"""Dictionary accuracy audit.

There is no gold RP reference to diff against, so we measure RULE CONFORMANCE:
for each sound that the spec says MUST carry a diacritic, check — across every
renderable CMUdict word — whether the engine actually marked it. Under-marking
(the sound is there in the pronunciation but no mark appears) is a real accuracy
defect. We use FULL density (everything markable is marked).

Run: python tools/accuracy_check.py
"""
import os, sys, cmudict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import engine

d = cmudict.dict()
COST = 2.6

# phoneme -> (marks that represent it, optional bare-acceptable substrings)
CHECKS = {
    "DH (voiced th /ð/)":  (["ħ"], []),
    "ZH (/ʒ/)":            (["ß"], []),
    "NG (/ŋ/)":            (["ñ"], []),
    "/ʌ/ (stressed AH)":   (list("âêîôûŷ"), []),
    "SH (/ʃ/)":            (["ş", "ç", "ť", "çh"], ["sh"]),
}

def stressed_AH(pron):
    return any(p in ("AH1", "AH2") for p in pron)

tally = {k: [0, 0, []] for k in CHECKS}   # name -> [hit, total, misses]
rendered = 0
for w, prons in d.items():
    if not w.isalpha() or len(prons) != 1:
        continue
    pron = prons[0]
    try:
        out, cost = engine.render(w.lower(), pron, full=True)
    except Exception:
        continue
    if out is None or cost > COST:
        continue
    rendered += 1
    stripped = [engine.strip_stress(p) for p in pron]

    for name, (marks, bares) in CHECKS.items():
        # does this word contain the target phoneme?
        if name.startswith("/ʌ/"):
            present = stressed_AH(pron)
        elif name.startswith("NG"):
            # NG present but NOT immediately before K (that case is correctly bare)
            present = any(stripped[i] == "NG" and not (i+1 < len(stripped) and stripped[i+1] == "K")
                          for i in range(len(stripped)))
        else:
            ph = name.split()[0]
            present = ph in stripped
        if not present:
            continue
        tally[name][1] += 1
        ok = any(mk in out for mk in marks) or any(b in out for b in bares)
        if ok:
            tally[name][0] += 1
        elif len(tally[name][2]) < 12:
            tally[name][2].append(f"{w}:{out}")

print("=" * 70)
print(f"DICTIONARY ACCURACY — rule-conformance audit ({rendered:,} renderable words)")
print("=" * 70)
print(f"{'sound (must be marked)':<26}{'marked':>16}   examples of MISSES")
print("-" * 70)
for name, (hit, tot, miss) in tally.items():
    rate = f"{hit}/{tot} ({100*hit/tot:.1f}%)" if tot else "n/a"
    print(f"{name:<26}{rate:>16}")
    if miss:
        print(f"    miss: {', '.join(miss[:6])}")
print("=" * 70)
