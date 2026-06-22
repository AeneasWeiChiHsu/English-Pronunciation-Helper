# -*- coding: utf-8 -*-
"""Dictionary accuracy audit (consonants + vowels).

No gold RP reference exists, so we measure RULE CONFORMANCE: for each sound the
spec says MUST carry a diacritic, check across every renderable CMUdict word
whether the engine actually marked it. Under-marking (sound present in the
pronunciation, no mark in the output) is a real accuracy defect. FULL density.

Run: python tools/accuracy_check.py
"""
import os, sys, cmudict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import engine

d = cmudict.dict()
COST = 2.6
MACRONS = "āēīōūȳ"
TILDES  = "ãẽĩõũỹ"

def has_any(out, chars):
    return any(c in out for c in chars)

# each check: (display, predicate(stripped, pron) -> bool present, ok(out) -> bool)
CHECKS = [
    ("DH  /ð/  voiced th",   lambda s,p: "DH" in s,
                             lambda o: "ħ" in o),
    ("ZH  /ʒ/",              lambda s,p: "ZH" in s,
                             lambda o: "ß" in o or "ǵ" in o or "ź" in o),
    ("NG  /ŋ/",              lambda s,p: any(s[i]=="NG" and not (i+1<len(s) and s[i+1]=="K") for i in range(len(s))),
                             lambda o: "ñ" in o),
    ("SH  /ʃ/",              lambda s,p: "SH" in s,
                             lambda o: has_any(o,"şçťħ") or "çh" in o or "sh" in o),
    ("/ʌ/  stressed AH",     lambda s,p: any(x in ("AH1","AH2") for x in p),
                             lambda o: has_any(o,"âêîôûŷ")),
    ("/ɜː/ stressed ER",     lambda s,p: any(x in ("ER1","ER2") for x in p),
                             lambda o: has_any(o, TILDES)),
    ("/ɔɪ/ OY",              lambda s,p: "OY" in s,
                             lambda o: "œ" in o),
    ("name vowels iy/ey/ay/ow", lambda s,p: any(x[:2] in ("IY","EY","AY","OW") and x[-1] in "12" for x in p),
                             lambda o: has_any(o, MACRONS) or has_any(o, "ïÿë")),
    ("/uː/ UW",              lambda s,p: "UW" in s,
                             lambda o: "ö" in o or has_any(o, MACRONS)),
    ("/aʊ/ AW",              lambda s,p: "AW" in s,
                             lambda o: "ü" in o or "ŵ" in o),
]

tally = [[0,0,[]] for _ in CHECKS]
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
    s = [engine.strip_stress(p) for p in pron]
    for k,(name,present,ok) in enumerate(CHECKS):
        if not present(s, pron):
            continue
        tally[k][1] += 1
        if ok(out):
            tally[k][0] += 1
        elif len(tally[k][2]) < 8:
            tally[k][2].append(f"{w}:{out}")

print("=" * 72)
print(f"DICTIONARY ACCURACY — rule-conformance audit ({rendered:,} renderable words)")
print("=" * 72)
print(f"{'sound (must be marked)':<28}{'marked':>16}")
print("-" * 72)
for (name,_,_), (hit,tot,miss) in zip(CHECKS, tally):
    rate = f"{hit}/{tot} ({100*hit/tot:.1f}%)" if tot else "n/a"
    print(f"{name:<28}{rate:>16}")
    if miss:
        print(f"    miss: {', '.join(miss[:6])}")
print("=" * 72)
