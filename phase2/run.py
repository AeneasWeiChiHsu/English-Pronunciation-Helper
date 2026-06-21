# -*- coding: utf-8 -*-
"""Phase-2 end-to-end runner.

    python phase2/run.py article.txt
    python phase2/run.py article.txt --density f
    MODEL=gemma3:12b python phase2/run.py article.txt   # calibration run
    python phase2/run.py article.txt --no-gemma         # spaCy-only / wiring test

Pipeline: segment -> gate -> disambiguate(spaCy + gemma) -> render
Prints the marked article + a dashboard report.
"""
import os, sys, json, argparse
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))

import segment, gate, render
from disambiguate import disambiguate
from ollama_client import MODEL, is_up

def load(density):
    base = json.load(open(os.path.join(ROOT, "extension", "base-dict.json")))["words"]
    hmap = json.load(open(os.path.join(ROOT, "data", "heteronym-map.json")))["map"]
    return base, hmap

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("article")
    ap.add_argument("--density", choices=["a", "f"], default="a")
    ap.add_argument("--no-gemma", action="store_true")
    args = ap.parse_args()

    text = open(args.article, encoding="utf-8").read()
    base, hmap = load(args.density)

    sentences, tokens = segment.segment(text)
    gated = gate.gate(tokens, base, hmap, density=args.density)
    g_stats = gate.stats(gated)
    het_report = disambiguate(gated, sentences, use_gemma=not args.no_gemma)
    marked = render.render(text, gated)

    print("=" * 70)
    print("MARKED ARTICLE")
    print("=" * 70)
    print(marked)
    print("\n" + "=" * 70)
    print("REPORT")
    print("=" * 70)
    print(f"model: {MODEL}   gemma reachable: {is_up()}   density: {args.density}")
    print(f"tokens: {len(tokens)}   sentences: {len(sentences)}")
    print(f"gate: {g_stats}")
    print(f"heteronyms -> spaCy {het_report['spacy']}, "
          f"gemma {het_report['gemma']}, fallback->bare {het_report['fallback']}")
    if het_report["decisions"]:
        print("decisions:")
        for d in het_report["decisions"]:
            print("   ", d)

if __name__ == "__main__":
    main()
