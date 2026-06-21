# CLAUDE.md — English Pronunciation-Guide Layer

> Read this first. It is the working context for this project. Your immediate
> job is in **§6 CURRENT TASK**. Do not start anywhere else without reason.

---

## 1. What this project is

A **peelable pronunciation-guide layer** for English. It overlays removable
diacritics onto *real* English spelling so that a reader can see how each word
is pronounced (British **RP**), then strip the marks to recover the exact
standard spelling. Example (advanced density):

```
plain :  The psychologist measured exposure to social media
layer :  The psȳčhòloǧist mèaßureď expōßure to sōçial mēdia
```

It targets **visual-first readers**: deaf/HoH people reading English by eye,
and CJK learners whose word-shape memory is strong but phonological intuition
is weak. Lineage: the same idea as Arabic *harakat* / Hebrew *niqqud* (removable
vowel pointing), not a spelling reform. It is **scaffolding**, meant to be
internalised then removed.

### SUPREME RULE — peelability (never violate)
Every mark is an overlay that can be stripped to return the original English
spelling **letter for letter**. Never substitute English letters; only add
removable diacritics. If a change can't be deterministically reversed to the
bookstore spelling, it is wrong. This single property is why the project exists
(it is what every failed alphabet-replacement scheme, e.g. ITA, lacked).

---

## 2. Repo map

```
extension/        Chrome MV3 extension (self-contained, load-unpacked ready)
  manifest.json, content.js, content.css, popup.html, popup.js, base-dict.json
src/
  engine.py             DP grapheme-phoneme aligner + rule engine (ARPAbet -> marks)
  build_full.py         CMUdict -> engine -> base-dict.json + outliers + heteronyms
  build_heteronym_map.py heteronym pronunciations + POS->variant map
spec/spelling-system.md  the full rule table ("the table" — required to read the marks)
data/
  outliers.json         words left bare (low-confidence / OOV)
  heteronyms.json        auto-detected heteronyms (stress-shift + 13 residual)
  heteronym-map.json     per-heteronym variants + pos_default mapping
phase2/                  Phase-2 context-aware heteronym disambiguation (see §5)
  segment.py gate.py disambiguate.py render.py ollama_client.py run.py README.md
```

---

## 3. Branches & current state

- **`main`** — stable: system + extension. Pushed.
- **`phase2-heteronyms`** — adds context-aware heteronym disambiguation
  (spaCy + local gemma2:2b via Ollama). Pushed. **Validated component-by-
  component** but the gemma layer has NOT yet been run end-to-end on the
  author's machine (the dev sandbox could not reach local Ollama).

GitHub: `https://github.com/AeneasWeiChiHsu/English-Pronunciation-Helper`

---

## 4. How the system works (offline build + runtime)

1. **Build (offline, ~4 min):** `python src/build_full.py` runs CMUdict
   (ARPAbet + stress) through `engine.py`. For each single-pron word the engine
   aligns letters↔phonemes (heuristic DP) and applies deterministic rules to
   emit `full` and `advanced` marked forms. Multi-pron weak/strong variants use
   the primary pronunciation; true heteronyms are excluded (→ Phase 2). Output:
   `extension/base-dict.json` (~93k words), `data/outliers.json`,
   `data/heteronyms.json`. Then `python src/build_heteronym_map.py`.
2. **Runtime (extension):** pure O(1) dictionary lookup, zero LLM. Miss → bare.
   `content.js` walks DOM text nodes, MutationObserver for SPAs, hover shows the
   original via `title`/`data-orig`, density toggle via `chrome.storage`.

**Rule changes:** edit `engine.py`, bump `RULE_VERSION`, re-run `build_full.py`
(+ `build_heteronym_map.py`), the extension reads the new `base-dict.json`.

---

## 5. Phase 2 — gated heteronym disambiguation

The base dict leaves ~920 heteronyms bare (record N/V, read past/present…)
because they need sentence context. Phase 2 resolves them:

```
article → segment → gate → disambiguate → render
                     (3 tables)  ├─ Layer 1 spaCy POS  → stress-shift resolved FREE
                                 └─ Layer 2 gemma2:2b  → leftovers + 13 vowel-residual
```

Design principles (do not regress these): **gated invocation** — ~95% of tokens
resolved by table lookup; of heteronyms, spaCy handles the stress-shift majority;
gemma is called only for the residual. **No long-term memory** — each sentence is
independent. Run:
```
python phase2/run.py <article.md>                 # gemma2:2b, advanced density
MODEL=gemma3:12b python phase2/run.py <article.md> # calibration vs 12b
python phase2/run.py <article.md> --no-gemma       # spaCy-only wiring test
```
Setup: `pip install -r phase2/requirements.txt`, `python -m spacy download
en_core_web_sm`, Ollama running with `gemma2:2b` pulled.

---

## 6. CURRENT TASK — finish Phase 2 and merge to main

Do these in order. Stop and report if anything in §7 would be violated.

1. **Confirm environment:** `ollama list` shows `gemma2:2b`; spaCy model
   installed. If not, run the setup in §5.
2. **End-to-end gemma run:** `python phase2/run.py <a real article>` on a
   machine where Ollama is reachable. Verify the report shows `gemma reachable:
   True` and that the vowel-residual heteronyms (e.g. `read`) are resolved by
   gemma (decisions show `by: gemma`), not `fallback->bare`. Spot-check 3–5
   decisions for correctness.
3. **2b vs 12b calibration (validates "no big model needed"):** run the same
   article with `MODEL=gemma3:12b`; diff the heteronym decisions against 2b.
   Record agreement rate. If ≥~90% agree, 2b is confirmed sufficient — note it
   in `phase2/README.md`.
4. **Tidy:** if anything failed, fix in `disambiguate.py` / `gate.py`. Keep the
   gated architecture (§5).
5. **Merge:** open/merge a PR `phase2-heteronyms → main` only after step 2
   passes. Update the root `README.md` with a short Phase-2 section + the
   pipeline diagram.

Definition of done: a real article runs end-to-end with gemma resolving the
residual heteronyms correctly, 2b-vs-12b agreement recorded, merged to main,
README updated.

---

## 7. Invariants — do NOT break these

- **Peelability (§1).** Any new rule must be deterministically reversible to
  standard spelling. No letter substitutions.
- **Bump `RULE_VERSION`** in `engine.py` whenever rules change, and rebuild the
  dictionaries; never hand-edit `base-dict.json`.
- **Never feed marked text to an LLM.** Marks inflate BPE tokens 3–4×. The marks
  are a human display layer; strip them (or use the original) for any machine
  consumer. (If touching the extension: keep the machine-readable layer = original.)
- **Engine is the single source of truth** for marks; the dictionary is a cache.
  Don't add ad-hoc marks outside the rule engine.
- **gemma is gated.** Don't make the pipeline call the LLM on every token or
  every heteronym; spaCy must stay the first filter.
- Don't commit `*.pem` keys or `epl-reports.json`.

---

## 8. Known limitations & the one open question

Field-wide problems (NOT bugs to "fix" naively): **/aʊ/ spelled "ow"** (down/now)
has no universal respelling solution; **TRAP–BATH** (last/dance) can't be derived
from American CMUdict — a curated BATH list is the only patch; **RP base vs
American CMUdict** mismatch (rhoticity handled; some vowels approximated).

**The one open question that matters most:** the core assumption — that *seeing
the marks helps people acquire pronunciation* (vs only reading correctly while
the marks are present) — is **unverified**. The decisive test is the "peel-off"
test: after practice, with marks removed, does a *non-author* user still
pronounce correctly? Treat this as the project's most important open item; do
not over-invest in features before it is tested. This is an assistive tool aimed
at vulnerable users (deaf/HoH, learners) and is offered as a free gift (MIT), so
validating real benefit is a responsibility, not just a nice-to-have.

---

## 9. Gotchas / lessons

- The build re-generates `base-dict.json`, `outliers.json`, `heteronyms.json`.
  Always re-run `build_heteronym_map.py` after `build_full.py`.
- When delivering files, never overwrite a folder with a partial copy — it can
  delete tracked files (this happened once; recovered via `git checkout main --`).
- `engine.py` uses a module-global for the current word during BATH lookup;
  it's single-threaded by design — don't parallelise render without fixing that.
- Heteronym detection rule (in `build_full.py`): a true stress-shift heteronym
  needs ≥2 syllables AND primary stress on ≥2 different positions across
  pronunciations. This excludes function words (the/a/to) that merely have
  weak/strong forms — don't loosen it.
```
