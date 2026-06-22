# -*- coding: utf-8 -*-
"""Wrong-mark audit: a mark is PRESENT but represents the WRONG sound.

The phoneme audit (accuracy_check) catches under-marking. This catches the
opposite: a letter-name macron whose glyph implies a sound the word doesn't
have. Each macron must co-occur with its phoneme; if the phoneme is absent,
the glyph is misleading (e.g. machine -> maçhīne: ī implies /aɪ/, word has /iː/).

Run: python tools/mismark_check.py
"""
import os, sys, cmudict
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import engine

d = cmudict.dict()
COST = 2.6

# glyph -> the phoneme it is supposed to mean (letter-name macrons)
MACRON_SOUND = {"ā": "EY", "ī": "AY", "ō": "OW", "ē": "IY", "ū": "UW", "ȳ": "AY",
                "ï": "IY", "ÿ": "IY", "ë": "EY"}

bad = {g: [0, []] for g in MACRON_SOUND}
present = {g: 0 for g in MACRON_SOUND}
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
    s = set(engine.strip_stress(p) for p in pron)
    for g, want in MACRON_SOUND.items():
        if g in out:
            present[g] += 1
            if want not in s:
                bad[g][0] += 1
                if len(bad[g][1]) < 10:
                    bad[g][1].append(f"{w}:{out}")

print("=" * 70)
print(f"WRONG-MARK AUDIT — macron glyph present but its sound absent ({rendered:,} words)")
print("=" * 70)
print(f"{'glyph (=sound)':<16}{'wrong / present':>20}")
print("-" * 70)
for g, want in MACRON_SOUND.items():
    n, ex = bad[g]
    tot = present[g]
    rate = f"{n}/{tot} ({100*n/tot:.1f}%)" if tot else "n/a"
    print(f"{g} = /{want}/{'':<8}{rate:>20}")
    if ex:
        print(f"    {', '.join(ex[:8])}")
print("=" * 70)
