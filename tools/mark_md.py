# -*- coding: utf-8 -*-
"""mark_md.py — apply the EPL pronunciation layer to a Markdown / plain-text
document, marking only the English prose and leaving everything else exact.

It is a thin, markdown-aware wrapper around the real engine (segment -> gate ->
disambiguate -> render): the engine stays the single source of truth, this file
adds no marks of its own. Protected (passed through untouched, peels back exact):

    - fenced code ```...``` / ~~~...~~~ and inline `code`
    - LaTeX  $...$  and  $$...$$
    - HTML comments <!-- ... -->  and tags <u> </u> <br> ...
    - the URL target of markdown links  [label](url)   (the label IS marked)
    - ALL-CAPS acronyms / model IDs  (NASA, DRAM, TSMC, A16)  -> left bare
    - runs of CJK / full-width characters (Chinese stays Chinese)

Peelability is GUARANTEED, not hoped for: every English gap is marked and then
each word is peel-checked; any word whose marks don't strip back to the exact
original is reverted to plain English. Worst case a gap is returned bare. This
makes the wrapper robust to any single-word engine glitch (e.g. acronym
case-folding) while never producing an unpeelable document.

Usage
-----
    python tools/mark_md.py article.md                 # -> stdout
    python tools/mark_md.py article.md -o article_epl.md
    python tools/mark_md.py article.md --density f      # full density
    cat article.md | python tools/mark_md.py            # stdin -> stdout

Exit status is non-zero if the whole-document peel check fails (it never should).
Note: the heteronym layer is gated off here (no per-sentence LLM); true
heteronyms therefore stay bare, consistent with 'never guess'. Run the Phase-2
pipeline if you need context-aware heteronym resolution.
"""
import os, sys, re, json, argparse, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "phase2"))
sys.path.insert(0, os.path.join(ROOT, "src"))
import segment, gate, render
from disambiguate import disambiguate

# ---- peelability: marked text -> standard English (mirrors epl.py) ----------
_SPECIAL = {"ħ": "h", "Ħ": "H", "ð": "d", "Ð": "D", "ß": "s", "œ": "o", "Œ": "O"}

def peel(marked):
    s = "".join(_SPECIAL.get(ch, ch) for ch in marked)
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return unicodedata.normalize("NFC", s)


class Engine:
    def __init__(self, density="a"):
        self.density = density
        self.base = json.load(open(os.path.join(ROOT, "extension", "base-dict.json")))["words"]
        self.hmap = json.load(open(os.path.join(ROOT, "data", "heteronym-map.json")))["map"]

    def mark(self, text):
        sentences, tokens = segment.segment(text)
        gated = gate.gate(tokens, self.base, self.hmap, density=self.density)
        disambiguate(gated, sentences, use_gemma=False)   # gated off -> residual bare
        return render.render(text, gated)


# Runs of CJK ideographs, Bopomofo, Kana and full-width punctuation.
CJK = r'[　-〿㄀-ㄯ㐀-䶿一-鿿豈-﫿︰-﹏＀-￯]'

def mask(text):
    """Replace every protected span with a NUL-delimited sentinel; return
    (masked_text, store)."""
    store = {}; n = [0]
    def repl(m):
        k = "\x00%d\x00" % n[0]; n[0] += 1; store[k] = m.group(0); return k
    text = re.sub(r'```.*?```', repl, text, flags=re.S)
    text = re.sub(r'~~~.*?~~~', repl, text, flags=re.S)
    text = re.sub(r'<!--.*?-->', repl, text, flags=re.S)
    text = re.sub(r'\$\$.*?\$\$', repl, text, flags=re.S)
    text = re.sub(r'`[^`\n]+`', repl, text)
    text = re.sub(r'\$[^$\n]+\$', repl, text)
    text = re.sub(r'\]\([^)\s]*\)', repl, text)        # ](url) link targets
    text = re.sub(r'<[^>\n]+>', repl, text)             # HTML tags
    text = re.sub(r'\b[A-Z][A-Z0-9]+\b', repl, text)    # ALL-CAPS acronyms / model IDs
    text = re.sub(CJK + r'+', repl, text)               # CJK / full-width runs
    return text, store


def safe_mark(eng, chunk):
    """Mark an English gap with a hard peelability guarantee."""
    if not chunk.strip():
        return chunk
    marked = eng.mark(chunk)
    if peel(marked) == chunk:
        return marked
    o = re.split(r'(\s+)', chunk)
    m = re.split(r'(\s+)', marked)
    if len(o) == len(m):
        cand = "".join(mw if peel(mw) == ow else ow for ow, mw in zip(o, m))
        if peel(cand) == chunk:
            return cand
    return chunk   # safe fallback: plain English


def process(src, density="a"):
    eng = Engine(density)
    masked, store = mask(src)
    out = []
    for p in re.split(r'(\x00\d+\x00)', masked):       # split so the engine never sees sentinels
        if re.fullmatch(r'\x00\d+\x00', p):
            out.append(store[p])                        # protected span -> verbatim
        elif p:
            out.append(safe_mark(eng, p))               # English gap -> marked, peel-guaranteed
    return "".join(out)


def main():
    ap = argparse.ArgumentParser(description="Apply the EPL layer to a Markdown/text document.")
    ap.add_argument("infile", nargs="?", help="input file (omit to read stdin)")
    ap.add_argument("-o", "--outfile", help="output file (default: stdout)")
    ap.add_argument("--density", choices=["a", "f"], default="a",
                    help="a = advanced (default), f = full")
    args = ap.parse_args()

    src = open(args.infile, encoding="utf-8").read() if args.infile else sys.stdin.read()
    out = process(src, args.density)

    ok = peel(out) == peel(src)   # both drop emoji variation selectors identically
    sys.stderr.write("[mark_md] peel check: %s\n" % ("OK" if ok else "FAIL"))

    if args.outfile:
        open(args.outfile, "w", encoding="utf-8").write(out)
        sys.stderr.write("[mark_md] wrote %s (%d chars)\n" % (args.outfile, len(out)))
    else:
        sys.stdout.write(out)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
