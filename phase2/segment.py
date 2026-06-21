# -*- coding: utf-8 -*-
"""Segment an article into sentences and word tokens, keeping char offsets
into the ORIGINAL string so render.py can splice replacements back in place
without disturbing punctuation/whitespace. No LLM needed."""
import re

_SENT = re.compile(r'[^.!?]*[.!?]+(?:\s|$)|[^.!?]+$', re.S)
_WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)?")

# spans that must NOT be marked (math/code/markup). Masked with equal-length
# spaces so offsets stay valid and no word tokens are emitted inside them.
_PROTECT = re.compile(
    r'\$\$.*?\$\$'              # display math
    r'|\$[^$\n]*?\$'           # inline math
    r'|`[^`\n]*`'              # inline code
    r'|\\[A-Za-z]+'           # LaTeX commands
    r'|<[^>\n]*>',            # HTML tags
    re.S)

def _protect(text):
    return _PROTECT.sub(lambda m: " " * len(m.group()), text)

def segment(text):
    masked = _protect(text)            # tokenize/POS on masked; render on original
    sentences, tokens = [], []
    for sid, sm in enumerate(_SENT.finditer(masked)):
        s_start, s_text = sm.start(), sm.group()
        if not s_text.strip():
            continue
        sentences.append({"sent_id": sid, "text": s_text, "start": s_start})
        for wm in _WORD.finditer(s_text):
            tokens.append({
                "text": wm.group(),
                "start": s_start + wm.start(),
                "end":   s_start + wm.end(),
                "sent_id": sid,
            })
    return sentences, tokens

if __name__ == "__main__":
    sents, toks = segment("I want to record a record. She read what you read.")
    print(len(sents), "sentences,", len(toks), "tokens")
    for t in toks[:6]:
        print(t)
