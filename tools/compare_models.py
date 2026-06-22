# -*- coding: utf-8 -*-
"""Compare LLMs on the Phase-2 heteronym disambiguation task.

Runs the gated pipeline on test-generated.txt with each model, grades the
vowel-residual decisions against a gold standard (we wrote the test text, so we
know the intended sense of every heteronym), and reports accuracy + latency.

Run: python tools/compare_models.py gemma2:2b llama3.1:8b
"""
import os, sys, json, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "phase2"))
sys.path.insert(0, os.path.join(ROOT, "src"))
import segment, gate
import ollama_client
import disambiguate as dis

base = json.load(open(os.path.join(ROOT, "extension", "base-dict.json")))["words"]
hmap = json.load(open(os.path.join(ROOT, "data", "heteronym-map.json")))["map"]
text = open(os.path.join(ROOT, "phase2", "test-generated.txt")).read()

# Gold: each vowel-residual occurrence in document order -> (sense, expected advanced mark)
GOLD = [
    ("read/past",      "read"),   ("read/present",   "rēad"),
    ("live/adj",       "līve"),   ("live/verb",      "live"),
    ("lead/metal",     "lead"),   ("lead/guide",     "lēad"),
    ("wind/air",       "wind"),   ("wind/twist",     "wīnd"),
    ("tear/drop",      "tear"),   ("tear/rip",       "tear"),
    ("bow/weapon",     "bōw"),    ("bow/bend",       "bow"),
    ("wound/injury",   "wöund"),  ("wound/windpast", "woünd"),
    ("sow/plant",      "sōw"),    ("sow/pig",        "sow"),
    ("close/shut",     "clōśe"),  ("close/near",     "clōse"),
    ("use/noun",       "ūse"),    ("use/verb",       "ūśe"),
]
RESIDUAL = {"read", "live", "lead", "wind", "tear", "bow", "wound", "sow", "close", "use"}

def run_model(model):
    ollama_client.MODEL = model
    dis.MODEL = model
    sentences, tokens = segment.segment(text)
    gated = gate.gate(tokens, base, hmap, density="a")
    t0 = time.time()
    report = dis.disambiguate(gated, sentences, use_gemma=True)
    dt = time.time() - t0
    # collect vowel-residual picks in document order
    picks = []
    for g in gated:
        lw = g["text"].lower().strip("'")
        if lw in RESIDUAL:
            picks.append(g.get("marked") or g["text"].lower())
    return picks, report, dt

models = sys.argv[1:] or ["gemma2:2b"]
results = {}
for mdl in models:
    print(f"running {mdl} ...", flush=True)
    results[mdl] = run_model(mdl)

# ---- report ----
print("\n" + "=" * 78)
print(f"{'heteronym (sense)':<20}{'gold':<10}" + "".join(f"{m:<16}" for m in models))
print("-" * 78)
score = {m: 0 for m in models}
for i, (sense, gold) in enumerate(GOLD):
    row = f"{sense:<20}{gold:<10}"
    for m in models:
        picks = results[m][0]
        got = picks[i] if i < len(picks) else "?"
        ok = (got == gold)
        score[m] += ok
        row += f"{(got + (' ✓' if ok else ' ✗')):<16}"
    print(row)
print("-" * 78)
n = len(GOLD)
for m in models:
    picks, report, dt = results[m]
    print(f"{m:<22} accuracy {score[m]}/{n} ({100*score[m]/n:.0f}%)   "
          f"gemma-calls {report['gemma']}   disambiguate {dt:.1f}s")
print("=" * 78)
