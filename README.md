# zhmd：中文學術寫作的後設論述量尺 / A Metadiscourse Scale for Chinese Academic Writing

> **這不是偵測器。This is not a detector.**
>
> 本工具產出的是描述性量尺與其失效條件，不能也不應該用來判定某篇文章是不是 AI 寫的。
> 個體之間的書寫差異大於機器與人類之間的差異，最突出的標記又因模型而異，翻譯稿件也會帶有同一批痕跡，
> 拿它判定作者身分，受害的往往是譯者與非母語書寫者。理由與證據見下方〈為什麼不做偵測器〉。
>
> This is a descriptive scale together with the conditions under which it fails. It cannot
> and must not be used to decide whether a text was written by AI. Individual variation
> exceeds the machine-human difference, the most prominent marker differs by model, and
> translated writing carries the same traces. Judging authorship this way harms translators
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

| 標記 | Hyland 範疇 | 實例 | 機器對人類率比 | 證據強度 |
|---|---|---|---|---|
| 累加轉折 | 引導式／轉折 | 不僅…更 | 8.22 | 強，留一來源穩健 |
| 視角框架 | 引導式／框架 | 在…脈絡下 | 6.79 | 強，留一來源穩健 |
| 引據標記 | 引導式／引據 | 有研究指出 | 6.71 | 強，留一來源穩健 |
| 語碼註解 | 引導式／語碼註解 | 破折號插入 | 4.29 | 中等，對來源敏感 |
| 對比重述 | 引導式／語碼註解 | 不是…而是 | 3.40 | 中等，對來源敏感 |
| 框架標記 | 引導式／框架 | 綜上所述 | 2.62 | 中等，其中最弱的一條 |
| 強調語 | 互動式／強調 | 至關重要 | 0.62 | 貝氏因子 8.96，支持無差異 |
| 態度標記 | 互動式／態度 | 值得注意的是 | 0.00 | 貝氏因子 3.47，支持無差異 |
| 模糊限制 | 互動式／模糊 | 可能、似乎 | 0.67 | 貝氏因子 1.65，證據不足 |
| 自稱 | 互動式／自稱 | 本研究、筆者 | 1.00 | 貝氏因子 14.76，支持無差異 |

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
與貝氏因子，其餘三條在移除單一模型之後就不顯著，上表的「證據強度」欄要跟率比一起讀。

**互動式標記的無差異有證據，但不是四條都有**。自稱、強調語與態度標記的貝氏因子支持無差異，
模糊限制語則只有 1.65，落在證據不足的區間，不能據以宣稱它沒有差異。

**正規表示式分不出使用與提及**。一篇討論「不僅…更」這個句式的文章，會被計為使用了它，
用 `--matches` 自己看過再判斷。

### 為什麼不做偵測器

其一，個體差異大於組間差異。以作者自身既有著作為基線的檢查顯示，其句長與句長變異落在語料的
第 100 百分位，個體差異達 2.1 倍，而機器與人類的句長比值僅 0.79，任何以個人為單位的判定
都會被書寫風格的正常變異淹沒。

其二，最突出的標記因模型而異。對比重述在大型商用模型上高達 11.85 倍，在小型模型上僅 1.45 倍，
任何固定門檻都會隨模型世代失效。

其三，翻譯會產生同一批痕跡。在與論文段落長度相當的英譯中樣本上，語碼註解達 4.30 倍，
對比重述達 2.94 倍，既有研究已證明商用偵測器會把非母語者的人類寫作大量誤判為機器產出
（Liang et al., 2023），以此判定將系統性地誤傷譯者與非母語書寫者。

其四，能被壓低的只有導覽密度。論點是否成立、證據是否充分、立場是否清楚，都不在量尺的測量範圍之內，
有人若拿本工具把標記密度壓低，該篇文章的論證品質並不會因此改變。

### 適合的用法

拿來當作者自己的鏡子，看看某個句式是不是已經成為書寫慣性，拿到寫作教學現場，
讓學生看見「更有條理」與「論點更強」是兩件事，或者用於語料層次的描述研究，比較兩批文本的分布，
而不是判定其中某一篇。

### 資料

本 repo 不含語料。論文所用的期刊論文有版權，機器生成文本與其提示語留在研究者本機，
這裡提供的是標記定義與計數統計程式，以及聚合之後的參考值（`reference.csv`）。

### 重現論文的數字

`stats.conditional_rr()` 預設只用零截斷負二項，與論文一致，
傳入 `fallback_poisson=True` 會在離散參數落於邊界時退回零截斷卜瓦松，一般使用較為方便，
但所得數字會偏離論文。

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
leave-one-source-out testing and Bayes factors: additive transition, perspective frame and
evidential. The other three lose significance once a single model is dropped. Read the evidence
column together with the rate ratio.

**The interactional nulls are evidenced, though not all four.** Bayes factors support no
difference for self-mentions (14.76), boosters (8.96) and attitude markers (3.47). Hedges sit
at 1.65, which settles nothing, so no claim of equivalence should be made there.

**Regular expressions cannot tell use from mention.** A paper discussing the 「不僅…更」
construction is counted as using it. Look at `--matches` before drawing conclusions.

### Why there is no detector here

Individual variation is larger than the group difference. Measured against the author's own
earlier writing, sentence length and its variability sit at the 100th percentile of the corpus,
a 2.1-fold individual difference, while the machine-human ratio for sentence length is 0.79.
Any judgement about a single person drowns in ordinary stylistic variation.

The most prominent marker depends on the model. Contrastive restatement reaches 11.85 in large
commercial models and 1.45 in a small one, so any fixed threshold expires with the next
generation of models.

Translation leaves the same traces. In Chinese translated from English at comparable length,
code glosses reach 4.30 and contrastive restatement 2.94. Commercial detectors are already known
to misclassify non-native human writing as machine-generated (Liang et al., 2023), and using
these markers the same way would repeat that harm.

Only navigational density can be lowered. Whether an argument holds, whether the evidence is
sufficient, whether a stance is clear: none of that lies inside what this scale measures. If
someone uses the tool to push marker density down, the quality of the argument is unchanged.

### Sensible uses

As a mirror for your own writing, to see whether a construction has become a habit. In writing
teaching, to show students that "better organised" and "better argued" are separate things. In
corpus-level description, to compare two sets of texts rather than to judge any single one.

### Data

No corpus is included. The journal articles are copyrighted and the generated texts stay on the
researcher's machine. What ships here is the marker definitions, the counting and statistics
code, and aggregate reference values in `reference.csv`.

### Reproducing the paper

`stats.conditional_rr()` uses zero-truncated negative binomial only, which is what the paper
did. Passing `fallback_poisson=True` falls back to a zero-truncated Poisson when the dispersion
parameter sits on its boundary. That is more convenient in general use and departs from the
published numbers.

---

## 引用 / Citation

見 `CITATION.cff`。請引用論文，而非僅引用本 repo。
See `CITATION.cff`. Please cite the paper rather than this repository alone.

## 授權 / License

程式碼採 MIT。標記定義與參考值另採 CC BY 4.0，可自由重用，請註明出處。
MIT for the code. The marker definitions and reference values are also released under
CC BY 4.0: reuse them freely, and say where they came from.
