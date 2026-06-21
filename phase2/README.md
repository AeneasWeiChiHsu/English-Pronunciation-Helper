# Phase 2 — Heteronym Disambiguation

Resolves the ~920 heteronyms (record N/V, read past/present, …) that the base
dictionary leaves bare, by looking at sentence context.

## Architecture (gated — gemma only when unavoidable)

```
article → segment → gate → disambiguate → render → marked article + report
                     │         │
            (no LLM, 3 tables)  ├─ Layer 1: spaCy POS  → resolves stress-shift heteronyms FREE
                                └─ Layer 2: gemma2:2b   → only leftovers + the 13 vowel-residual
```

~95% of tokens are resolved by the gate (table lookup). Of the heteronyms,
the stress-shift majority is resolved by spaCy POS; gemma handles only the
residual. No long-term memory: each sentence is independent.

## Setup
```bash
pip install -r phase2/requirements.txt
python -m spacy download en_core_web_sm
ollama pull gemma2:2b        # Ollama must be running (localhost:11434)
```

## Run
```bash
python phase2/run.py article.txt                 # advanced density, gemma2:2b
python phase2/run.py article.txt --density f      # full density
MODEL=gemma3:12b python phase2/run.py article.txt # calibration vs 12b
python phase2/run.py article.txt --no-gemma       # spaCy-only (wiring test)
```

Outputs the marked article + a report: how many heteronyms, how many resolved
by spaCy vs gemma, and each decision.

## Components
- `segment.py` — sentences + word tokens with char offsets (no LLM)
- `gate.py` — 3-table lookup → render / bare / heteronym (no LLM)
- `disambiguate.py` — spaCy POS (Layer 1) + Ollama gemma2:2b (Layer 2)
- `render.py` — splice marks back by offset (no LLM)
- `ollama_client.py` — local Ollama caller, format:json, MODEL switch
- `run.py` — orchestrator

## Validated
- segment/gate/render + spaCy: stress-shift heteronyms (record/present/object) resolved correctly, 0 gemma calls.
- gemma2:2b on real hardware: read→past, record(noun ctx)→noun, record(verb ctx)→verb, all correct, ~270–330ms/call warm.
