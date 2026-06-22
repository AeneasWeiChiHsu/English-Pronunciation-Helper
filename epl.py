# -*- coding: utf-8 -*-
"""epl.py — engine test bench (private, not the shipped extension).

Type a sentence, get back the marked version. Same pipeline the extension/
Phase-2 use (segment -> gate -> disambiguate -> render), so what you test here
is what the engine actually produces — this is a probe, not a second engine.

Usage
-----
    python epl.py "your sentence here"      # one-shot
    echo "piped text" | python epl.py       # stdin
    python epl.py                           # interactive REPL (loads once, stays warm)

REPL commands
-------------
    :q            quit
    :d            toggle density  advanced <-> full
    :g            toggle gemma heteronym layer on/off
    :v            toggle verbose (per-word breakdown + heteronym decisions)
    :h            help

Every output line is peel-checked: the marks are stripped and compared to your
original input. PEEL OK means the supreme invariant held (reversible to exact
English); PEEL FAIL flags a word whose marks don't strip back cleanly.
"""
import os, sys, json, argparse, unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "phase2"))
sys.path.insert(0, os.path.join(HERE, "src"))

import segment, gate, render
from disambiguate import disambiguate
from ollama_client import MODEL, is_up

# ---- peelability: marked text -> original English ---------------------------
# Variant letters that do NOT reduce to ASCII by stripping combining marks.
_SPECIAL = {
    "ħ": "h", "Ħ": "H",      # h-bar  -> voiced th (tħe)
    "ð": "d", "Ð": "D",      # eth    -> dge  (jûðge)
    "ß": "s",                # eszett -> /ʒ/  (meaßure)
    "œ": "o", "Œ": "O",      # /ɔɪ/ rides the first vowel; the i stays (chœice->choice)
}

def peel(marked):
    """Strip every overlay back to standard English spelling, letter for letter."""
    s = "".join(_SPECIAL.get(ch, ch) for ch in marked)
    # decompose, drop combining marks (the diacritics), recompose
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", s)


class Engine:
    def __init__(self, density="a", use_gemma=True):
        self.density = density
        self.use_gemma = use_gemma
        self.base = json.load(open(os.path.join(HERE, "extension", "base-dict.json")))["words"]
        self.hmap = json.load(open(os.path.join(HERE, "data", "heteronym-map.json")))["map"]

    def mark(self, text):
        sentences, tokens = segment.segment(text)
        gated = gate.gate(tokens, self.base, self.hmap, density=self.density)
        report = disambiguate(gated, sentences, use_gemma=self.use_gemma)
        marked = render.render(text, gated)
        return marked, gated, report


def _peel_check(original, marked):
    """Return (ok, [(orig_word, peeled_word) ...]) for any word that fails to peel."""
    o = original.split()
    m = marked.split()
    bad = []
    if len(o) == len(m):
        for ow, mw in zip(o, m):
            if peel(mw) != ow:
                bad.append((ow, peel(mw)))
    return (len(bad) == 0), bad


def show(engine, text, verbose=False):
    text = text.rstrip("\n")
    if not text.strip():
        return
    marked, gated, report = engine.mark(text)
    print(marked)

    ok, bad = _peel_check(text, marked)
    tag = "PEEL OK" if ok else "PEEL FAIL"
    print(f"  [{tag}]", end="")
    if bad:
        print("  " + ", ".join(f"{o!r}->{p!r}" for o, p in bad[:6]), end="")
    print()

    if verbose:
        acts = gate.stats(gated)
        print(f"  gate: {acts}  |  heteronyms: spaCy {report['spacy']}, "
              f"gemma {report['gemma']}, bare {report['fallback']}")
        for g in gated:
            a = g.get("action")
            if a == "render":
                print(f"     {g['text']:<16} -> {g.get('marked')}")
            elif a == "bare":
                print(f"     {g['text']:<16} .  (bare)")
        for d in report["decisions"]:
            print(f"     · {d}")


def repl(engine):
    warm = "True" if (engine.use_gemma and is_up()) else "False"
    print(f"epl test bench — model {MODEL}, gemma reachable {warm}, "
          f"density {engine.density}, gemma {'on' if engine.use_gemma else 'off'}")
    print("type a sentence, or :h for commands, :q to quit\n")
    while True:
        try:
            line = input("epl> ")
        except (EOFError, KeyboardInterrupt):
            print()
            break
        s = line.strip()
        if s in (":q", ":quit", ":exit"):
            break
        elif s == ":h":
            print(__doc__)
            continue
        elif s == ":d":
            engine.density = "f" if engine.density == "a" else "a"
            print(f"  density -> {engine.density}")
            continue
        elif s == ":g":
            engine.use_gemma = not engine.use_gemma
            print(f"  gemma -> {'on' if engine.use_gemma else 'off'}")
            continue
        elif s == ":v":
            engine._verbose = not getattr(engine, "_verbose", False)
            print(f"  verbose -> {engine._verbose}")
            continue
        show(engine, line, verbose=getattr(engine, "_verbose", False))


def main():
    ap = argparse.ArgumentParser(description="epl engine test bench")
    ap.add_argument("sentence", nargs="*", help="sentence to mark (omit for REPL/stdin)")
    ap.add_argument("--density", choices=["a", "f"], default="a")
    ap.add_argument("--no-gemma", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    engine = Engine(density=args.density, use_gemma=not args.no_gemma)

    if args.sentence:                       # one-shot from argv
        show(engine, " ".join(args.sentence), verbose=args.verbose)
    elif not sys.stdin.isatty():            # piped stdin
        for line in sys.stdin:
            show(engine, line, verbose=args.verbose)
    else:                                   # interactive
        engine._verbose = args.verbose
        repl(engine)


if __name__ == "__main__":
    main()
