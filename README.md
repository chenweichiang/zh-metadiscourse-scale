# zhmd：中文學術寫作的後設論述量尺 / A Metadiscourse Scale for Chinese Academic Writing

> **這不是偵測器。This is not a detector.**
>
> 本工具產出的是描述性量尺與其失效條件，不能也不應該用來判定某篇文章是不是 AI 寫的。
> 單一作者的書寫差異可以大過機器與人類之間的差異，最突出的標記又因模型而異，翻譯也會帶出同一批痕跡，
> 拿它判定作者身分，受害的往往是譯者與非母語書寫者。理由與證據見下方〈為什麼不做偵測器〉。
>
> This is a descriptive scale together with the conditions under which it fails. It cannot
> and must not be used to decide whether a text was written by AI. One writer's own variation
> can exceed the machine-human difference, the most prominent marker differs by model, and
> translation brings in the same traces. Judging authorship this way harms translators
> and non-native writers first. See *Why there is no detector here*.

---

## 中文

### 這是什麼

本工具是一組十條中文後設論述標記的定義與計數程式，用途在於把「這段文字像是 AI 寫的」這種讀者判斷，
轉成可以計量比較、也能指出何時失效的數字。標記依 Hyland 的後設論述框架分為兩類，
引導式（interactive）標記帶著讀者穿過文本，包含轉折、框架、引據與語碼註解，
互動式（interactional）標記則表達作者立場，包含模糊限制語、強調語、態度標記與自稱。
本工具是論文〈「AI 味」作為新的感性對象〉的隨附程式，該文所報告的率比、柵欄模型與貝氏因子皆由此處產生。

### 安裝

```bash
pip install -e .
```

需要 Python 3.10 以上，相依套件為 numpy、pandas 與 statsmodels。

### 用法

```bash
zhmd 我的論文.txt
zhmd 我的論文.txt --matches      # 連實際匹配一併列出，供人工判讀
```

```python
from zhmd import profile, stats

r = profile(open("我的論文.txt", encoding="utf-8").read())
r["per15k"]["累加轉折"]        # 換算成每 15,000 漢字的次數
r["interactive_total"]         # 六條引導式標記的合計

irr, lo, hi, p = stats.irr(counts, group, han)   # 兩組文本的率比，以文本長度的對數為偏移項
```

### 十條標記

| 標記 | Hyland 範疇 | 實例 | 率比：本機模型 | 率比：含商用模型 | 證據強度（本機模型） |
|---|---|---|---|---|---|
| 累加轉折 | 引導式／轉折 | 不僅…更 | 8.22 | 6.32 | 強，留一來源穩健 |
| 視角框架 | 引導式／框架 | 在…脈絡下 | 6.79 | 5.39 | 強，留一來源穩健 |
| 引據標記 | 引導式／引據 | 有研究指出 | 6.71 | 6.56 | 強，留一來源穩健 |
| 語碼註解 | 引導式／語碼註解 | 破折號插入 | 4.29 | 4.44 | 中等，對來源敏感 |
| 對比重述 | 引導式／語碼註解 | 不是…而是 | 3.40 | 4.94 | 中等，對來源敏感 |
| 框架標記 | 引導式／框架 | 綜上所述 | 2.62 | 1.52 | 中等，其中最弱的一條；含商用模型後不顯著 |
| 強調語 | 互動式／強調 | 至關重要 | 0.62 | 0.50 | 貝氏因子 8.96，支持無差異 |
| 態度標記 | 互動式／態度 | 值得注意的是 | —（零次） | 4.29 | 本機模型 48 篇零次出現，無法估計；含商用模型後顯著偏高 |
| 模糊限制 | 互動式／模糊 | 可能、似乎 | 0.67 | 0.99 | 貝氏因子 1.65，證據不足；含商用模型後為 13.36，支持無差異 |
| 自稱 | 互動式／自稱 | 本研究、筆者 | 1.00 | 0.83 | 貝氏因子 14.76，支持無差異 |

人類基線是 2018 至 2022 年的 122 篇期刊論文。「本機模型」是三個本機開放權重模型（gemma4、gpt-oss、
gpt-oss-120b）的 48 篇，「含商用模型」再加上 gpt-5.1、gpt-5-mini、Claude Opus 5 與 Claude Sonnet 5
的 64 篇。論文、`reference.csv` 與證據強度欄都以本機模型為準；納入商用模型後，態度標記、框架標記與
模糊限制三條的結論會改變，引用時請寫明比較的是哪一組模型。態度標記在本機模型的文本裡一次都沒出現，
`reference.csv` 該列的 0.00 與貝氏因子 3.47 都是估計發散的結果，不能讀成兩組相同。

信賴區間與其餘參考值見 `src/zhmd/reference.csv`。社群清單裡的「虛假範圍」曾被納入，
但抽樣顯示約半數匹配為誤判，例如「從上述結果可得知」的「到」並非範圍端點，該標記因此剔除，
本工具刻意不提供它，測試中也擋著它復活。

### 怎麼讀這些數字

**長度決定你讀得到什麼**，這是本工具最重要的使用限制。三百漢字的文本裡，有出現某條標記的文本
幾乎全部只出現一次，累加轉折為 95.2%，對比重述與視角框架則是百分之百，換算到全文層級才降至
38.4% 至 67.3%。「用了幾次」這個量在短文本上根本不存在，摘要長度的文本因此只能讀「有沒有用」，
全文長度才能讀「用得多密」，而全文才是學術寫作實際被評斷的單位。`conditional_rr()` 在這種情況下
回傳 `NaN`，不會硬給一個數字。

**證據強度並不相同**。六條引導式標記裡只有累加轉折、視角框架與引據標記三條同時通過留一來源檢定
（在三個本機模型之間輪流剔除一個）與貝氏因子，其餘三條在移除單一模型之後就不顯著，
上表的「證據強度」欄要跟率比一起讀。

**互動式標記的無差異只有兩條站得住**。自稱與強調語的貝氏因子支持無差異（14.76、8.96），
納入商用模型後仍是如此（9.89、3.28）。態度標記在本機模型的文本裡一次都沒出現，無從比較，
商用模型則用得明顯較多。模糊限制語在本機模型只有 1.65，落在證據不足的區間，
納入商用模型後才升到 13.36，結論取決於比較哪些模型。

**正規表示式分不出使用與提及**。一篇討論「不僅…更」這個句式的文章，會被計為使用了它，
用 `--matches` 自己看過再判斷。

### 為什麼不做偵測器

其一，單一作者的書寫差異可以大過機器與人類之間的差異。以本工具作者 2022 至 2023 年親寫的三篇
中文論文為例，平均句長 114.8 漢字，是期刊中位數的 2.1 倍，句長與句長變異都落在期刊語料的
第 100 百分位，而機器與人類的句長比值只有 0.79。拿群體基線判定這三篇，它們會因為句子太長、
長短落差太大而被標成異常。這是單一作者的例子，作者的著作與計算句長所需的人類原文都不在本 repo，
這組數字無法在此重算；它說明的是以個人為單位判定時，書寫風格的正常變異足以蓋過機器與人類的差距。

其二，最突出的標記因模型而異。對比重述在 gpt-5.1 的文本裡是人類基線的 8.18 倍，同一家的
gpt-5-mini 只有 1.37 倍，七個模型之間從 1.06 倍（gpt-oss-120b）到 8.18 倍不等，
任何固定門檻都會隨模型世代失效。論文報告的 11.85 與 1.45 是把兩組文本都裁到約 1,400 漢字後的比較，
人類原文不在本 repo，這裡改報可以重算的全長數字。

其三，翻譯本身就會推高其中幾條標記。gemma4 把英文論文段落譯成中文的 15 篇譯文，
語碼註解是三個本機模型中文原生文本的 4.30 倍，對比重述是 2.94 倍；譯文短到摘要長度（42 篇）時，
兩者都測不到差異。這組比較的譯者是模型，比較對象也是模型自己寫的中文，它只顯示這些標記會隨翻譯而來，
真人譯稿並未測量。真人譯者與非母語書寫者面臨的風險另有證據：既有研究已證明商用偵測器會把
非母語者的人類寫作大量誤判為機器產出（Liang et al., 2023），拿這些標記判定作者，最先受害的也會是他們。

其四，能被壓低的只有導覽密度。論點是否成立、證據是否充分、立場是否清楚，都不在量尺的測量範圍之內，
有人若拿本工具把標記密度壓低，該篇文章的論證品質並不會因此改變。

### 適合的用法

拿來當作者自己的鏡子，看看某個句式是不是已經成為書寫慣性，拿到寫作教學現場，
讓學生看見「更有條理」與「論點更強」是兩件事，或者用於語料層次的描述研究，比較兩批文本的分布，
而不是判定其中某一篇。

### 資料

本 repo 不含人類語料。論文所用的 184 篇期刊論文有版權，`data/human_article_list.csv` 列出每一篇的書目，
可自行向期刊網站下載。機器端的文本則全數收錄：`data/machine_texts/` 是研究用的 201 篇生成與翻譯文本，
`data/marker_counts.csv` 是全部 385 篇的逐篇計數，說明見 `data/README.md`；生成用的提示語全文未收錄。
另附標記定義與計數統計程式，以及聚合之後的參考值（`reference.csv`）。

### 重現論文的數字

`stats.conditional_rr()` 預設只用零截斷負二項，與論文一致，
傳入 `fallback_poisson=True` 會在離散參數落於邊界時退回零截斷卜瓦松，一般使用較為方便，
但所得數字會偏離論文。

本 README 各數字的重算步驟寫在 `tests/readme_repro.py`，執行 `python tests/readme_repro.py`
會印出對照表，`tests/test_readme_numbers.py` 鎖住這些數字。唯一無法在此重算的是
〈為什麼不做偵測器〉其一的句長數字。

---

## English

### What this is

Definitions and counting code for ten metadiscourse markers of Chinese academic writing.
The point is to turn a reader's sense that a passage "reads like AI" into numbers that can be
measured, compared, and shown to fail. Markers follow Hyland's two-way split: interactive
markers guide readers through a text, covering transitions, frame markers, evidentials and
code glosses; interactional markers convey stance, covering hedges, boosters, attitude markers
and self-mentions. This code accompanies the paper *AI-Sounding Text as a New Kansei Object*,
and every rate ratio, hurdle model and Bayes factor reported there was produced with it.

### Install

```bash
pip install -e .
```

Python 3.10 or later, with numpy, pandas and statsmodels.

### Use

```bash
zhmd paper.txt
zhmd paper.txt --matches     # also print the actual matches, for manual checking
```

```python
from zhmd import profile, stats

r = profile(text)
r["per15k"]["累加轉折"]      # occurrences per 15,000 Chinese characters
r["interactive_total"]       # sum over the six interactive markers

irr, lo, hi, p = stats.irr(counts, group, han)   # log-length offset throughout
```

### How to read the numbers

**Length decides what is readable at all.** In 300-character texts, 95 to 100 per cent of the
texts that use a marker use it exactly once; at full-text length that share falls to between
38 and 67 per cent. "How often" is therefore not a smaller signal in short text, it is not a
quantity that exists there. Abstract-length text supports only whether a marker occurs,
full-length text supports how densely it is used, and full length is the unit by which academic
writing actually gets judged. Where the conditional rate cannot be identified,
`conditional_rr()` returns `NaN` instead of inventing a number.

**Evidence strength differs by marker.** Of the six interactive markers, three survive both
leave-one-source-out testing (dropping each of the three local models in turn) and Bayes
factors: additive transition, perspective frame and evidential. The other three lose
significance once a single model is dropped. Read the evidence column together with the rate
ratio.

**Which models count as "machine" matters.** The table in the Chinese section gives two rate
ratios per marker against 122 human journal articles from 2018 to 2022: one for the three local
open-weight models (gemma4, gpt-oss, gpt-oss-120b; 48 texts), and one with four commercial
models added (gpt-5.1, gpt-5-mini, Claude Opus 5, Claude Sonnet 5; 64 more texts). The paper,
`reference.csv` and the evidence column use the local models. Adding the commercial models
changes three conclusions: attitude markers, frame markers and hedges. Say which set of models
you are citing.

**Only two interactional nulls hold up.** Bayes factors support no difference for
self-mentions (14.76) and boosters (8.96), and still do once the commercial models are added
(9.89 and 3.28). Attitude markers never occur in the local models' texts, so there is nothing to
compare; the 0.00 and 3.47 in `reference.csv` come from an estimate that diverged and do not mean
the groups are alike. The commercial models use attitude markers considerably more often
(rate ratio 4.29). Hedges sit at 1.65 for the local models, which settles nothing, and reach
13.36 only when the commercial models are added.

**Regular expressions cannot tell use from mention.** A paper discussing the 「不僅…更」
construction is counted as using it. Look at `--matches` before drawing conclusions.

### Why there is no detector here

One writer's own variation can exceed the machine-human difference. Take three Chinese papers
the author of this tool wrote in 2022 and 2023: mean sentence length is 114.8 characters,
2.1 times the journal median, and both sentence length and its variability sit at the 100th
percentile of the journal corpus. The machine-human ratio for sentence length is 0.79. Judged
against the group baseline, those papers would be flagged as anomalous for long and uneven
sentences. This is a single writer, and neither the author's papers nor the human articles
needed for sentence length are in this repository, so these figures cannot be recomputed here.
What the example shows is that ordinary stylistic variation can outweigh the machine-human gap
once the unit of judgement is a person.

The most prominent marker depends on the model. Contrastive restatement is 8.18 times the human
baseline in gpt-5.1 text and 1.37 in gpt-5-mini from the same vendor; across the seven models it
ranges from 1.06 (gpt-oss-120b) to 8.18. Any fixed threshold expires with the next generation of
models. The paper reports 11.85 and 1.45 after truncating both sides to about 1,400 characters;
the human articles are not in this repository, so the full-length figures, which can be
recomputed, are given here.

Translation raises some of these markers by itself. In 15 English paper paragraphs translated
into Chinese by gemma4, code glosses are 4.30 times and contrastive restatement 2.94 times as
frequent as in the three local models' own Chinese writing. In abstract-length translations
(42 texts) neither difference is detectable. The translator here is a model and the comparison
is the models' own Chinese, so this shows the markers arriving with translation; human
translations were not measured. The risk to human translators and non-native writers rests on
separate evidence: commercial detectors already misclassify non-native human writing as
machine-generated (Liang et al., 2023), and judging authorship by these markers would hit the
same writers first.

Only navigational density can be lowered. Whether an argument holds, whether the evidence is
sufficient, whether a stance is clear: none of that lies inside what this scale measures. If
someone uses the tool to push marker density down, the quality of the argument is unchanged.

### Sensible uses

As a mirror for your own writing, to see whether a construction has become a habit. In writing
teaching, to show students that "better organised" and "better argued" are separate things. In
corpus-level description, to compare two sets of texts rather than to judge any single one.

### Data

No human corpus is included. The 184 journal articles are copyrighted;
`data/human_article_list.csv` identifies each one, and all can be downloaded from the journals.
The machine side is included in full: `data/machine_texts/` holds the 201 generated and
translated texts, and `data/marker_counts.csv` has per-text counts for all 385 texts (see
`data/README.md`). The prompts used for generation are not included. Also shipped: the marker
definitions, the counting and statistics code, and aggregate reference values in
`reference.csv`.

### Reproducing the paper

`stats.conditional_rr()` uses zero-truncated negative binomial only, which is what the paper
did. Passing `fallback_poisson=True` falls back to a zero-truncated Poisson when the dispersion
parameter sits on its boundary. That is more convenient in general use and departs from the
published numbers.

Every number in this README is recomputed by `tests/readme_repro.py` (run
`python tests/readme_repro.py` for a side-by-side table) and pinned by
`tests/test_readme_numbers.py`. The sentence-length figures in the first point of *Why there is
no detector here* are the only exception.

---

## 引用 / Citation

見 `CITATION.cff`。請引用論文，而非僅引用本 repo。
See `CITATION.cff`. Please cite the paper rather than this repository alone.

## 授權 / License

程式碼採 MIT。標記定義與參考值另採 CC BY 4.0，可自由重用，請註明出處。
MIT for the code. The marker definitions and reference values are also released under
CC BY 4.0: reuse them freely, and say where they came from.
