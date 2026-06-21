# -*- coding: utf-8 -*-
"""render.py — splice marks back into the ORIGINAL text by offset (right-to-left
so earlier offsets stay valid). Preserves all whitespace/punctuation exactly."""

def render(text, gated):
    edits = [(g["start"], g["end"], g["marked"])
             for g in gated if g.get("action") == "render" and g.get("marked")]
    edits.sort(key=lambda e: e[0], reverse=True)
    out = text
    for start, end, marked in edits:
        out = out[:start] + marked + out[end:]
    return out
