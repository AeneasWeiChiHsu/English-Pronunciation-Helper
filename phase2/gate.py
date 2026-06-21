# -*- coding: utf-8 -*-
"""The gate (no LLM). For each token decide one of:
   - 'render'    : found in base-dict -> use the precomputed mark
   - 'bare'      : common-law / outlier / not found -> leave as-is
   - 'heteronym' : in heteronym-map -> needs disambiguation (-> disambiguate.py)
This is where ~95% of tokens are resolved without ever touching gemma."""

def _cap(orig, marked):
    if orig[:1].isupper() and marked[:1].islower():
        return marked[0].upper() + marked[1:]
    return marked

def gate(tokens, base_words, het_map, density="a"):
    out = []
    for t in tokens:
        w = t["text"]
        lw = w.lower().strip("'")
        rec = dict(t)
        if lw in het_map:
            rec["action"] = "heteronym"
            rec["het"] = het_map[lw]
        elif lw in base_words:
            e = base_words[lw]
            marked = e["f"] if density == "f" else e["a"]
            rec["action"] = "render"
            rec["marked"] = _cap(w, marked) if marked != lw else None
            if rec["marked"] is None:
                rec["action"] = "bare"
        else:
            rec["action"] = "bare"           # common-law / outlier / OOV
        out.append(rec)
    return out

def stats(gated):
    from collections import Counter
    c = Counter(g["action"] for g in gated)
    return dict(c)
