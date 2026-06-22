# -*- coding: utf-8 -*-
"""Engine performance harness. Measures the things that actually matter:
   1. Peelability at scale  — peel(mark) == original for ALL ~93k dict entries
   2. Coverage              — % of words marked on natural text
   3. Edge cases            — contractions, caps, hyphens, numbers
   4. Speed                 — tokens/sec through gate (no LLM)
   5. Pron spot-check       — a random sample to eyeball by hand
Run: python tools/perf_test.py
"""
import os, sys, json, time, unicodedata, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "phase2"))
import segment, gate

# --- peel (inlined, no heavy imports) ---------------------------------------
_SPECIAL = {"ħ": "h", "Ħ": "H", "ð": "d", "Ð": "D", "ß": "s", "œ": "o", "Œ": "O"}
def peel(marked):
    s = "".join(_SPECIAL.get(ch, ch) for ch in marked)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", s)

base = json.load(open(os.path.join(ROOT, "extension", "base-dict.json")))["words"]
hmap = json.load(open(os.path.join(ROOT, "data", "heteronym-map.json")))["map"]

def bar(n, d):
    return f"{n}/{d} ({100*n/d:.2f}%)" if d else "0/0"

print("=" * 64)
print("ENGINE PERFORMANCE REPORT")
print("=" * 64)
print(f"dictionary entries: {len(base):,}   heteronym map: {len(hmap):,}")

# --- ROUND 1: peelability of every entry, both densities --------------------
print("\n[Round 1] Peelability audit — every dict entry must strip to itself")
for dens in ("f", "a"):
    fails = []
    marked_cnt = 0
    for k, e in base.items():
        form = e[dens]
        if form != k:
            marked_cnt += 1
        if peel(form) != k:
            fails.append((k, form, peel(form)))
    ok = len(base) - len(fails)
    label = "full" if dens == "f" else "advanced"
    print(f"  {label:<9} peel-clean: {bar(ok, len(base))}   marked: {bar(marked_cnt, len(base))}")
    for k, f, p in fails[:8]:
        print(f"      FAIL {k!r} -> mark {f!r} -> peel {p!r}")
    if len(fails) > 8:
        print(f"      ... +{len(fails)-8} more")

# --- ROUND 2: coverage on natural text --------------------------------------
print("\n[Round 2] Coverage on natural text (marked vs bare)")
corpus = open(os.path.join(ROOT, "tools", "corpus.txt")).read()
_, tokens = segment.segment(corpus)
gated = gate.gate(tokens, base, hmap, density="a")
from collections import Counter
c = Counter(g["action"] for g in gated)
tot = len(tokens)
print(f"  tokens: {tot}   "
      f"render(marked): {bar(c.get('render',0), tot)}   "
      f"bare: {bar(c.get('bare',0), tot)}   "
      f"heteronym: {bar(c.get('heteronym',0), tot)}")

# --- ROUND 3: edge cases ----------------------------------------------------
print("\n[Round 3] Edge cases — peelability on tricky tokens")
edge = ("Don't panic — it's the U.S.A.! The 24-hour, well-meaning, "
        "ALL-CAPS HEADLINE read 100% fine, didn't it? Co-operate, please.")
_, etok = segment.segment(edge)
eg = gate.gate(etok, base, hmap, density="f")
efails = [(g["text"], g.get("marked")) for g in eg
          if g.get("action") == "render" and g.get("marked")
          and peel(g["marked"]) != g["text"]]
emarked = [(g["text"], g["marked"]) for g in eg if g.get("action") == "render" and g.get("marked")]
print(f"  edge tokens marked: {len(emarked)}   peel failures: {len(efails)}")
for t, m in efails:
    print(f"      FAIL {t!r} -> {m!r} -> {peel(m)!r}")
print("  samples: " + ", ".join(f"{t}->{m}" for t, m in emarked[:8]))

# --- ROUND 4: speed ---------------------------------------------------------
print("\n[Round 4] Speed (gate throughput, no LLM)")
big = corpus * 20
_, btok = segment.segment(big)
t0 = time.time()
gate.gate(btok, base, hmap, density="a")
dt = time.time() - t0
print(f"  {len(btok):,} tokens in {dt*1000:.1f} ms  ->  {len(btok)/dt:,.0f} tokens/sec")

# --- ROUND 5: pronunciation spot-check sample -------------------------------
print("\n[Round 5] Random marked-word sample (eyeball pron correctness)")
random.seed(7)
marked_words = [(k, e["a"]) for k, e in base.items() if e["a"] != k and len(k) > 3]
for k, m in random.sample(marked_words, 25):
    print(f"      {k:<16} -> {m}")
print("=" * 64)
