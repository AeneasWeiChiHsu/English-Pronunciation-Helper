# -*- coding: utf-8 -*-
"""
English Pronunciation-Guide Layer — build engine.
CMUdict (ARPAbet + stress) --align--> per-letter sounds --rules--> marked spelling.
Two densities: full / advanced. Outliers (multi-pron or low-confidence) -> 素顏.
"""
import re

RULE_VERSION = "v1.4"

VOWELS_AR = {"AA","AE","AH","AO","AW","AY","EH","ER","EY","IH","IY","OW","OY","UH","UW"}

def strip_stress(ph):
    return re.sub(r"\d","",ph)

def stress_of(ph):
    m = re.search(r"(\d)", ph)
    return int(m.group(1)) if m else None

# ---------- grapheme<->phoneme correspondence table (cost: lower=better) ----------
# key: grapheme string ; value: set of acceptable stripped-phoneme tuples
CORR = {
    # single vowels
    "a": {("AE",),("EY",),("AA",),("AH",),("AO",),("EH",),("IH",),("ER",)},
    "e": {("EH",),("IY",),("IH",),("AH",),("ER",),()},
    "i": {("IH",),("AY",),("IY",),("AH",),("ER",)},
    "o": {("AA",),("OW",),("AH",),("AO",),("UW",),("UH",),("ER",),("W","AH")},
    "u": {("AH",),("UW",),("UH",),("Y","UW"),("W",),("ER",),("IH",)},
    "y": {("IH",),("AY",),("IY",),("AH",),("ER",)},
    # vowel digraphs
    "ee":{("IY",)}, "ea":{("IY",),("EH",),("EY",),("IH",)}, "ai":{("EY",),("EH",)},
    "ay":{("EY",)}, "oo":{("UW",),("UH",)}, "ou":{("AW",),("UW",),("AH",),("AO",),("OW",),("UH",)},
    "ow":{("AW",),("OW",)}, "oa":{("OW",)}, "oe":{("OW",),("UW",)}, "au":{("AO",),("AE",),("AA",)},
    "aw":{("AO",),("AA",)}, "oy":{("OY",)}, "oi":{("OY",)}, "ei":{("EY",),("IY",),("AY",)},
    "ey":{("EY",),("IY",)}, "ie":{("AY",),("IY",),("IH",)}, "ue":{("UW",),("Y","UW")},
    "ui":{("UW",),("IH",)}, "eu":{("Y","UW"),("UW",)}, "eau":{("Y","UW"),("OW",)},
    # consonants single
    "b":{("B",),()}, "c":{("K",),("S",),("SH",),("CH",)}, "d":{("D",),("JH",),("T",),()},
    "f":{("F",)}, "g":{("G",),("JH",),("ZH",),()}, "h":{("HH",),()}, "j":{("JH",),("Y",)},
    "k":{("K",),()}, "l":{("L",),()}, "m":{("M",)}, "n":{("N",),("NG",)},
    "p":{("P",),()}, "q":{("K",)}, "r":{("R",),()}, "s":{("S",),("Z",),("SH",),("ZH",)},
    "t":{("T",),("D",),("CH",),("SH",),()}, "v":{("V",)}, "w":{("W",),()},
    "x":{("K","S"),("G","Z"),("Z",),("K","SH")}, "z":{("Z",),("ZH",),("S",)},
    # consonant digraphs / clusters
    "ss":{("S",),("SH",),("Z",)},
    "th":{("TH",),("DH",)}, "sh":{("SH",)}, "ch":{("CH",),("K",),("SH",)}, "ph":{("F",)},
    "gh":{("F",),("G",),()}, "ck":{("K",)}, "ng":{("NG",),("N","G")}, "qu":{("K","W"),("K",)},
    "wh":{("W",),("HH",)}, "tch":{("CH",)}, "dge":{("JH",)}, "wr":{("R",)}, "kn":{("N",)},
    "mb":{("M",)}, "mn":{("M",)}, "ti":{("SH",),("SH","IY"),("SH","AH")}, "ci":{("SH",)},
    "si":{("ZH",),("SH",)}, "ssi":{("SH",)}, "sci":{("SH",)}, "xi":{("K","SH")},
    "tu":{("CH",),("CH","ER"),("CH","UW")}, "su":{("ZH",),("SH",)}, "que":{("K",)},
    "le":{("AH","L"),("L",)}, "el":{("AH","L"),("L",)}, "on":{("AH","N"),("AA","N")},
}

def corr_cost(g, p):
    p = tuple(strip_stress(x) for x in p)
    opts = CORR.get(g)
    if opts is None:
        return 6.0
    if p in opts:
        # prefer longer grapheme + nonempty for tie-break handled by length bonus
        return 0.0
    # partial: empty grapheme matching empty
    if p == () and () in opts:
        return 0.0
    return 4.0

def align(word, phones):
    """DP align letters<->phonemes. Returns list of (graph, [phones])."""
    w = word.lower()
    P = phones
    n, m = len(w), len(P)
    INF = float("inf")
    # dp[i][j] = best cost aligning w[:i], P[:j]
    dp = [[INF]*(m+1) for _ in range(n+1)]
    bk = [[None]*(m+1) for _ in range(n+1)]
    dp[0][0] = 0.0
    for i in range(n+1):
        for j in range(m+1):
            if dp[i][j] == INF: continue
            base = dp[i][j]
            for gl in range(0,4):          # consume gl letters (0..3)
                for pl in range(0,3):      # consume pl phonemes (0..2)
                    if gl==0 and pl==0: continue
                    ni, nj = i+gl, j+pl
                    if ni>n or nj>m: continue
                    g = w[i:ni]
                    p = tuple(P[j:nj])
                    c = corr_cost(g, p)
                    # length bonus: reward consuming both
                    c += 0.05*(2 - min(gl,1) - min(pl,1))
                    # mild penalty for pure insert/delete
                    if gl==0: c += 2.0
                    if pl==0 and g not in ("e","gh","b","h","k","l","w","u","t","r","n") : c += 1.0
                    if base + c < dp[ni][nj]:
                        dp[ni][nj] = base + c
                        bk[ni][nj] = (i,j,g,list(p))
    # backtrack
    if dp[n][m] == INF:
        return None, INF
    path = []
    i,j = n,m
    while not (i==0 and j==0):
        pi,pj,g,p = bk[i][j]
        path.append((g,p))
        i,j = pi,pj
    path.reverse()
    return path, dp[n][m]

# ---------- RP-ish patch sets ----------
BATH = set("""after answer ask aunt bath basket blast branch brass cannot cant cast castle
chance chant class clasp craft dance demand draft draught example fast fasten France
glance glass grasp grass half lance last mast master nasty pass past path pasture plant
raft rascal rather rasp staff task vast advance advantage afterward broadcast command
disaster enchant overcast outlast playground rather sample slander slant telegraph """.split())

# ---------- rule engine ----------
GRAVE = {"a":"à","e":"è","i":"ì","o":"ò","u":"ù","y":"ỳ"}
MACRON_LETTERNAME = {  # vowel letter -> its 'name' mark (used for EY/AY/OW/etc by letter)
    "a":"ā","e":"ē","i":"ī","o":"ō","u":"ū","y":"ȳ"}
CIRC = {"a":"â","e":"ê","i":"î","o":"ô","u":"û","y":"ŷ"}
TILDE = {"a":"ã","e":"ẽ","i":"ĩ","o":"õ","u":"ũ","y":"ỹ"}
RING = {"a":"å"}
BREVE = {"a":"ă"}

def mark_vowel_letters(g, ph_list, stress, is_poly, letters_before, letters_after, full):
    """Return marked grapheme for a vowel chunk. ph_list = stripped phones (no R)."""
    g = g.lower()
    # collapse to the primary vowel phoneme present
    vows = [p for p in ph_list if p in VOWELS_AR]
    has_r = any(p=="R" for p in ph_list)
    if not vows:
        return g  # e.g. silent
    v = vows[0]
    out = list(g)
    # choose index of letter to carry mark: first vowel letter in g
    vi = next((k for k,ch in enumerate(g) if ch in "aeiouy"), 0)
    base_letter = g[vi]

    def put(mapping, fallback=None):
        ch = mapping.get(base_letter)
        if ch is None and fallback is not None:
            ch = fallback
        if ch:
            out[vi] = ch

    marked = False
    # ----- quality marks (self-imply stress) -----
    if v=="IY":
        if base_letter=="y" and stress==0:
            marked=False
        elif full:
            put(MACRON_LETTERNAME); marked=True
        elif stress in (1,2):
            put(MACRON_LETTERNAME); marked=True
    elif v=="EY":
        put(MACRON_LETTERNAME); marked=True             # ā
    elif v=="AY":
        put(MACRON_LETTERNAME); marked=True             # ī (on i/y)
    elif v=="OW":
        put(MACRON_LETTERNAME); marked=True             # ō
    elif v=="UW":
        # Y UW -> /juː/ ū ; plain UW -> /uː/ ö
        if "Y" in ph_list:
            put(MACRON_LETTERNAME); marked=True          # ū
        else:
            if "o" in g: out[g.index("o")]="ö"; marked=True
            elif "u" in g: out[g.index("u")]="ū"; marked=True   # approx
            else: put(MACRON_LETTERNAME); marked=True
    elif v=="AW":
        # /aʊ/ : ou-> ü on u ; ow -> leave (gap) ; else mark first
        if "ou" in g: out[g.index("u")]="ü"; marked=True
        else: marked=False   # ow / others: leave 素顏 (known gap)
    elif v=="OY":
        out[vi]="œ" if base_letter=="o" else out[vi]; marked=True
        if "oi" in g: pass
    elif v=="ER":
        # /ɜː/ tilde at primary OR secondary stress ; unstressed -> schwa+r (素顏)
        if stress in (1,2):
            put(TILDE); marked=True
        else:
            marked=False  # ER0 schwa+r, bare
    elif v=="AH":
        if stress in (1,2):
            put(CIRC); marked=True            # /ʌ/ circumflex on its letter
        else:
            marked=False                       # schwa -> bare
    elif v=="AA":
        if base_letter=="a":                   # /ɑː/ -> å
            if full or True: out[vi]="å"; marked=True
        else:                                  # spelled o -> /ɒ/ bare
            marked=False
    elif v=="AO":
        # /ɔː/ vs /ɒ/(RP). spelled with a/w/u/r -> /ɔː/ keep bare; spelled o -> /ɒ/ bare
        marked=False
    elif v=="AE":
        if word_l in BATH and base_letter=="a":
            out[vi]="å"; marked=True            # BATH -> /ɑː/
        else:
            marked=False                        # /æ/ bare
    elif v in ("EH","IH","UH"):
        marked=False                            # short, bare
    # ----- stress grave (only if not quality-marked, polysyllabic, primary stress) -----
    if (not marked) and stress==1 and is_poly:
        g2 = GRAVE.get(base_letter)
        if g2: out[vi]=g2
    return "".join(out)

word_l = ""  # set per word

def render(word, phones, full=True):
    global word_l
    word_l = word.lower()
    path, cost = align(word_l, phones)
    if path is None:
        return None, cost
    # syllable count = number of vowel phonemes
    nsyl = sum(1 for p in phones if strip_stress(p) in VOWELS_AR)
    is_poly = nsyl >= 2
    # precompute phoneme stream flags for context (NG before K, etc.)
    out_chunks = []
    # flatten for lookahead
    for idx,(g,p) in enumerate(path):
        gl = g.lower()
        ps = [strip_stress(x) for x in p]
        stress = None
        for x in p:
            s = stress_of(x)
            if s is not None: stress = s if stress is None else max(stress,s)
        if gl=="":
            out_chunks.append(g); continue
        has_vowel_phone = any(x in VOWELS_AR for x in ps)
        if not has_vowel_phone:
            out_chunks.append(mark_consonant(gl, ps, path, idx)); continue
        out_chunks.append(mark_vowel_letters(g, ps, stress, is_poly, "", "", full))
    s = "".join(out_chunks)
    # ----- -ed past tense pass -----
    s = ed_pass(s, word_l, phones)
    return s, cost

def next_phones(path, idx):
    out=[]
    for g,p in path[idx+1:]:
        out += [strip_stress(x) for x in p]
    return out

def mark_consonant(gl, ps, path, idx):
    nxt = next_phones(path, idx)
    # th
    if gl=="th":
        if "DH" in ps: return "tħ"
        return "th"
    if gl=="s":
        if "Z" in ps: return "ś"
        if "ZH" in ps: return "ß"
        if "SH" in ps: return "ş"
        return "s"
    if gl=="ss":
        if "SH" in ps: return "sş"
        if "Z" in ps: return "sś"
        return "ss"
    if gl in ("ti","ci","ssi","sci"):
        if "SH" in ps:
            # render: keep letters, put ť on t / ç on c / ş on the 2nd s of ss
            if gl=="ti": return "ťi"
            if gl=="ssi": return "sşi"          # ss-family /ʃ/: prèsşure, mìsşion
            return gl.replace("c","ç",1)        # ci, sci
        return gl
    if gl=="tu":
        if "CH" in ps: return "ṫu"
        return gl
    if gl=="su":
        if "ZH" in ps: return "ßu"
        if "SH" in ps: return "şu"
        return gl
    if gl=="si":
        if "ZH" in ps: return "ßi"      # vißion, decißion, occaßion  (-sion /ʒ/)
        if "SH" in ps: return "şi"      # tènşion, mànşion, apprehènşion  (-sion /ʃ/)
        return gl
    if gl=="c":
        if "S" in ps: return "ç"
        if "SH" in ps: return "ç"
        return "c"          # K -> bare
    if gl=="g":
        if "ZH" in ps: return "ǵ"      # /ʒ/  garage, mirage, genre (g-acute: voiced fricative, cf. ś)
        if "JH" in ps: return "ǧ"      # /dʒ/ magic (caron)
        return "g"          # hard /g/ bare (exception dot ġ omitted for simplicity here)
    if gl=="z":
        if "ZH" in ps: return "ź"      # /ʒ/  azure, seizure (z-acute, same voiced-fricative family)
        return "z"          # /z/ bare
    if gl=="ch":
        if "CH" in ps: return "ċh"
        if "K" in ps:  return "čh"
        if "SH" in ps: return "çh"
        return "ch"
    if gl=="tch":
        return "tċh" if "CH" in ps else "tch"
    if gl=="dge":
        return "ðge" if "JH" in ps else "dge"
    if gl=="ng":
        if "NG" in ps:
            if nxt[:1]==["K"]:   # ng before k -> bare
                return "ng"
            return "ñg"
        return gl
    if gl=="n":
        if "NG" in ps:
            if nxt[:1]==["K"]: return "n"
            return "ñ"
        return "n"
    return gl

def ed_pass(s, word, phones):
    if not word.endswith("ed"):
        return s
    ps = [strip_stress(p) for p in phones]
    # syllabic /ɪd/ : ends ...(IH|AH) D
    if len(ps)>=2 and ps[-1]=="D" and ps[-2] in ("IH","AH"):
        return s            # plain ed
    if ps[-1] in ("T","D"):
        # non-syllabic -> e silent -> eď   (mark the final d)
        # replace trailing 'ed' rendering's d with ď
        return re.sub(r"d$","ď", s)
    return s

# quick self-test
if __name__=="__main__":
    import cmudict
    d = cmudict.dict()
    tests = ["rising","designed","technology","pleasure","magic","nation","future",
             "something","others","burnout","cycle","measure","exposure","political",
             "responses","cats","dogs","please","walked","wanted","loved","father",
             "last","car","thinking","anger","church","chemistry","chef","judge",
             "about","computer","sufficiently","exacerbated"]
    for w in tests:
        pr = d.get(w)
        if not pr:
            print(f"{w:16} (not in dict)"); continue
        if len(pr)>1:
            print(f"{w:16} OUTLIER ({len(pr)} prons)"); continue
        full,c = render(w, pr[0], full=True)
        adv,_  = render(w, pr[0], full=False)
        print(f"{w:16} full={full:18} adv={adv:18} cost={c:.2f}")
