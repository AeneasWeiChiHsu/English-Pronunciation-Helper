# -*- coding: utf-8 -*-
"""Thin Ollama client. Talks to the local Ollama HTTP server (localhost:11434).

Default model gemma2:2b (the disambiguation task is a 'gimme' — no big model
needed). Set MODEL=gemma3:12b to run the calibration comparison.
"""
import os, json, urllib.request

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
MODEL      = os.environ.get("MODEL", "gemma2:2b")   # switch to gemma3:12b to compare

def ask_json(prompt, model=None, timeout=60):
    """Send a prompt, force JSON output, return parsed dict (or {} on failure)."""
    body = json.dumps({
        "model": model or MODEL,
        "prompt": prompt,
        "format": "json",          # grammar-constrained -> always valid JSON
        "stream": False,
        "options": {"temperature": 0, "num_predict": 64},
    }).encode()
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            resp = json.loads(r.read())
        return json.loads(resp.get("response", "{}"))
    except Exception as e:
        return {"_error": str(e)}

def is_up():
    try:
        urllib.request.urlopen(OLLAMA_URL.replace("/api/generate", "/api/tags"), timeout=3)
        return True
    except Exception:
        return False
