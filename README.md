# English Pronunciation-Guide Layer · 英文發音導引層

> **A peelable pronunciation layer you can put on, then take off.**
> Worn, it shows you how every English word sounds. Peeled, what's left is exactly standard English — every book on the shelf.
>
> **一層可以戴上、也可以摘下的發音圖層。**
> 戴上時,它告訴你每個英文字怎麼念;摘下時,剩下的就是標準英文——書架上的每一本書。

Reference accent: **British RP** · 基準口音:**英式 RP**
License: **MIT** (free for everyone, forever · 永久免費,隨便用)

---

## What it looks like · 長什麼樣

It overlays diacritics on real English spelling. Hover any word to see the original.
它把變音符號疊在真正的英文拼寫上。Hover 任何字就能看到原拼。

```
plain :  The psychologist measured exposure to social media
layer :  The psȳčhòloǧist mèaßureď expōßure to sōçial mēdia
```

The marks encode **stress** (grave: `ò`), **long vowels** (macron = letter's name `ā ē ī ō ū`,
diaeresis = the other long vowel `ï ÿ` /iː/, `ë` /eɪ/), **/aʊ/** (`oü` / `ŵ` for *how→hoŵ*),
**/ʌ/** (`û ô`), **voiced th** (`tħ`), **s/z/ʒ** (`ś ş ß`), **soft c/g and /ʒ/** (`ç ǧ ǵ ź`), and more.
Strip every mark and you get the bookstore spelling back, letter for letter.

記號標的是**重音**(grave:`ò`)、**長母音**(macron=唸本名 `ā ē ī ō ū`、diaeresis=另一個長音 `ï ÿ`=/iː/、`ë`=/eɪ/)、
**/aʊ/**(`oü` / `ŵ`,如 *how→hoŵ*)、**/ʌ/**(`û ô`)、**濁 th**(`tħ`)、**s 三值**(`ś ş ß`)、**軟 c/g 與 /ʒ/**(`ç ǧ ǵ ź`)等等。
把記號全部剝掉,就一字不差地還原成書店裡的拼法。

---

## Quick start · 快速上手

**Install the Chrome / Edge extension · 安裝瀏覽器擴充**

1. Download or `git clone` this repo · 下載或 clone 這個 repo
2. Open `chrome://extensions` → enable **Developer mode** · 開啟「開發人員模式」
3. **Load unpacked** → select the `extension/` folder · 「載入未封裝項目」→ 選 `extension/` 資料夾
4. Click the toolbar icon → pick a density → browse any English page
   點工具列圖示 → 選密度 → 看任何英文網頁

That's it. The `extension/` folder is self-contained (dictionary bundled).
就這樣。`extension/` 資料夾是自帶字典、開箱即用的。

---

## Using it · 使用方式

- **Hover** any marked word → tooltip shows the original spelling (this is what *peelable* means).
  **Hover** 任何標記字 → tooltip 顯示原拼(這就是「可剝離」的意思)。
- **Density toggle** in the popup · popup 裡切換密度:
  - **Advanced** — marks only the "deceptive" cases (default). · **進階** — 只標「會騙人的」(預設)。
  - **Full** — marks everything that changes sound. · **全標** — 每個會變音的都標。
  - **Off** — plain English. · **關閉** — 純英文。
  Density switching is instant (no reload). · 密度切換即時生效,免 reload。
- **Alt + click** a word → logs it for review; export the list from the popup.
  **Alt + 點**一個字 → 記下它待檢查;popup 可匯出清單。

---

## The rules · 規則表

The full specification lives in [`spec/spelling-system.md`](spec/spelling-system.md).
完整規格在 [`spec/spelling-system.md`](spec/spelling-system.md)。

This system is **hard to reverse-engineer without the table, but instant once you have it** —
the rules are deterministic and closed, with built-in mnemonics (e.g. `^` echoes IPA /ʌ/,
the háček marks "departure from default"). It is **scaffolding**: learn the table, internalise it,
then peel it off — like macrons in *Wheelock's Latin* or zhuyin in children's books.

這套系統**沒有表幾乎無法逆推,但拿到表就秒懂**——規則是封閉、確定的,而且有助記邏輯
(例如 `^` 呼應 IPA 的 /ʌ/、háček 標「偏離預設」)。它是**鷹架**:學會表、內化、然後摘掉——
就像《Wheelock's Latin》的長短音、童書裡的注音符號。

---

## Coverage & accuracy · 覆蓋率與正確率 (v1.7)

**Peelability — the supreme invariant — holds at 100%:** all 95,757 dictionary
entries strip back to the exact original spelling, letter for letter (audited every build).

**Rule-conformance accuracy** (does each sound that must be marked actually get marked,
across ~94k words): every markable sound is at **100%** — `/ð/ /ŋ/ /ʌ/ /ɜː/ /ʒ/ /ɔɪ/ /uː/ /aʊ/`
and the whole long-vowel family — **except `/ʃ/` at 99.1%** (the residual is `xi`/`xu` in
*anxious*/*complexion*, which have no `s` letter to decorate — a true peelability limit).

可剝離(最高法則)維持 **100%**(95,757 字全可逆);**標記正確率**:每個該標的音都 **100%**,
唯 `/ʃ/` 99.1%(殘量是 *anxious* 的 `xi`,無 s 可標的物理極限)。

Words the dictionary can't render with confidence (rare alignments, true heteronyms needing
context) are left **unmarked** — the system **never guesses**; when unsure, it shows plain English.

字典無法有把握渲染的字(罕見對齊、需上下文的真異音字)一律**素顏**——系統**從不亂猜**。

> Audited by `tools/perf_test.py` (peelability), `tools/accuracy_check.py` (under-marking),
> and `tools/mismark_check.py` (wrong-mark). Rebuild: `python src/build_full.py`.

---

## Rebuild from source · 從原始碼重建

The dictionary is generated, not hand-written. · 字典是算出來的,不是手打的。

```bash
pip install -r requirements.txt
python src/build_full.py        # writes extension/base-dict.json + data/*.json
```

- `src/engine.py` — the aligner + rule engine (ARPAbet → marks). Edit rules here, then bump `RULE_VERSION`.
- `src/build_full.py` — runs CMUdict through the engine (~1–4 min on a modern laptop).

To change the system: edit `engine.py` → bump `RULE_VERSION` → re-run `build_full.py` →
reload the extension (`chrome://extensions` → reload → refresh the page).

改系統:改 `engine.py` → bump `RULE_VERSION` → 重跑 `build_full.py` → 重載擴充。

**Heteronyms** (record-noun vs record-verb) are auto-detected from CMUdict by comparing stress
placement across pronunciations — **1,019** found automatically, plus a residual list of **13**
same-stress cases. See `data/heteronyms.json`.

**異音字**(record 名詞 vs 動詞)由機器從 CMUdict 比對重音位置自動偵測——自動抓到 **1,019** 個,
外加 **13** 個同重音殘量。見 `data/heteronyms.json`。

---

## Phase 2 — context-aware heteronyms · 異音字情境消歧

The base dictionary leaves true heteronyms (`record` N/V, `read` past/present)
**bare**, because their pronunciation needs sentence context. Phase 2 resolves
them with a **gated** pipeline — cheap layers first, the LLM only as a last resort:

```
article → segment → gate → disambiguate → render
                    (tables)  ├─ spaCy POS   → stress-shift heteronyms, free
                              └─ gemma2:2b   → the residual (read/live/wind…)
```

~95% of tokens resolve by table lookup; of the heteronyms, spaCy handles the
stress-shift majority and a local **gemma2:2b** (via Ollama) handles only the
vowel residual. No long-term memory — each sentence is independent.

```bash
pip install -r phase2/requirements.txt && python -m spacy download en_core_web_sm
python phase2/run.py phase2/test-generated.txt          # gemma2:2b, advanced density
MODEL=gemma3:12b python phase2/run.py <article>         # calibration vs 12b
```

**Validated end-to-end** on a synthetic, bias-free test passage: gemma2:2b
correctly disambiguates read/live/lead/wind/wound/close (both senses); **2b vs
12b agree on 93.5% of decisions** → the small local model is sufficient. Details
in `phase2/README.md`.

基準字典把真異音字(`record` 名/動、`read` 過去/現在)留**素顏**,因為要靠句子情境。
Phase 2 用**閘控**管線消歧:先查表、spaCy 判詞性,只有母音殘量才丟本機 **gemma2:2b**。
合成、無選文偏差的測試驗證:2b 與 12b 決策一致率 **93.5%** → 小模型就夠。

---

## Repo structure · 專案結構

```
extension/   Chrome/Edge MV3 extension (self-contained, load-unpacked)
src/         engine.py (rules) + build_full.py (dictionary builder)
data/        outliers.json, heteronyms.json (review data)
phase2/      context-aware heteronym disambiguation (spaCy + gemma2:2b)
spec/        spelling-system.md (the full rule table)
tools/       perf_test, accuracy_check, mismark_check (audits) + corpus
epl.py       engine test bench — sentence in → marked out, REPL, peel-check
```

---

## Who it's for · 給誰用

- **Deaf / hard-of-hearing readers** accessing English visually — the strongest use case.
  **聾人 / 聽障讀者**用視覺讀英文——最強的應用場景。
- **CJK learners** whose visual word-shape memory is strong but phonological intuition is weak.
  **CJK 學習者**——字形視覺記憶強、但拼讀直覺弱的人。
- **Pronunciation teaching** — a way to make stress, vowel length, and voiced/voiceless `th` visible.
  **發音教學**——把重音、母音長短、清濁 `th` 攤開來給學生看。

---

## An honest note · 一點誠實話

This is a **gift, not a product**, and it ships with one untested assumption:
**we don't yet know whether seeing the marks actually helps people *acquire* pronunciation**,
as opposed to just reading correctly *while the marks are there*. It might be a crutch you can
put down (good), or one you come to depend on (a risk, especially for visual-first learners).
If you build on this or share it, the most valuable thing you can do is **test the "peel-off"
question** with real users: after practice, with the marks removed, do they still pronounce correctly?

這是一份**禮物,不是產品**,而且它帶著一個尚未驗證的假設:
**我們還不知道「看記號」是否真能幫人『習得』發音**,還是只是「有記號時念得對」而已。
它可能是放得下的拐杖(好),也可能變成會依賴的東西(風險,對視覺優先的學習者尤其如此)。
如果你要在此基礎上開發或分享,最有價值的一件事是**做「剝掉測試」**:
練一陣子後把記號拿掉,使用者還念得準嗎?

---

## Contributing · 參與

Found a word that's marked wrong, or should be marked but isn't? Alt-click it in the extension to
log it, export the list, and open an issue — or edit the rules in `src/engine.py` and rebuild.

發現標錯、或該標卻沒標的字?在擴充裡 Alt-點它記下來、匯出清單、開 issue——
或直接改 `src/engine.py` 的規則重建。
