"""Marker definitions / 標記定義.

Ten Chinese realisations of Hyland's metadiscourse categories.
以正規表示式實作的十條中文後設論述標記，對應 Hyland (2005) 與 Hyland & Tse (2004)
的引導式（interactive）與互動式（interactional）兩大類。

Validity notes / 效度備註
    每條標記在論文中抽 12 個實際匹配人工判讀，多數全數正確。
    Two changes resulted from that check:
      * 「虛假範圍」(false range, "from X to Y") was DROPPED — about half of its
        matches were false positives. It is deliberately absent here.
      * 「引據標記」originally included 普遍認為／一般認為; sampling showed these
        usually describe research data (「受試者普遍認為…」) rather than
        unsourced attribution, so they were removed.

    Regular expressions cannot tell USE from MENTION. A text that discusses the
    marker 「不僅…更」will be counted as using it.
    正規表示式無法區分句式的「使用」與「提及」。
"""

from __future__ import annotations

import re

#: Chinese character class used as the exposure unit / 曝光量的計算單位
HAN = re.compile(r"[一-鿿]")

#: Same-sentence span cap for paired constructions / 需前後呼應之框架的同句跨度上限
NEAR = r"[^。！？\n]{0,30}"

INTERACTIVE = "interactive"
INTERACTIONAL = "interactional"

#: name -> (pattern, Hyland category, subcategory, English gloss)
MARKERS: dict[str, tuple[str, str, str, str]] = {
    "累加轉折": (rf"不僅{NEAR}(?:更|也還|還|也)", INTERACTIVE, "transitions",
             "additive transition, 'not only ... but also'"),
    "對比重述": (rf"(?:不是|並非|不只是|不僅僅是){NEAR}(?:而是|而在於)", INTERACTIVE, "code glosses",
             "contrastive restatement, 'not X but Y'"),
    "框架標記": (r"(?:綜上所述|總的來說|總而言之|整體而言|由此可見|本文旨在|首先.{0,8}其次)",
             INTERACTIVE, "frame markers", "frame marker, 'in sum'"),
    "語碼註解": (r"——|(?<!—)—(?!—)", INTERACTIVE, "code glosses",
             "code gloss via em-dash insertion"),
    "引據標記": (r"(?:有學者認為|有研究指出|眾多研究顯示|文獻指出|研究顯示)",
             INTERACTIVE, "evidentials", "evidential, 'research suggests'"),
    "視角框架": (rf"(?:在{NEAR}(?:脈絡|框架|語境|視角|維度)下|從{NEAR}(?:視角|角度)(?:出發|來看))",
             INTERACTIVE, "frame markers", "perspective frame, 'in the context of'"),
    "強調語": (r"(?:至關重要|不可或缺|極為重要|深刻地|全方位|高度重視|無疑|必然)",
            INTERACTIONAL, "boosters", "booster, 'crucial'"),
    "態度標記": (r"(?:值得注意的是|需要注意的是|必須指出的是|重要的是要|令人驚訝的是)",
             INTERACTIONAL, "attitude markers", "attitude marker, 'notably'"),
    "模糊限制": (r"(?:可能|或許|也許|似乎|大致|傾向於|在某種程度上|某種程度而言|不一定|未必|大體上)",
             INTERACTIONAL, "hedges", "hedge, 'may/seem'"),
    "自稱": (r"(?:本研究|本文|筆者|我們認為|作者認為)", INTERACTIONAL, "self-mentions",
           "self-mention, 'this study'"),
}

_COMPILED = {k: re.compile(v[0]) for k, v in MARKERS.items()}

INTERACTIVE_MARKERS = [k for k, v in MARKERS.items() if v[1] == INTERACTIVE]
INTERACTIONAL_MARKERS = [k for k, v in MARKERS.items() if v[1] == INTERACTIONAL]


def han_length(text: str) -> int:
    """Number of Chinese characters / 漢字數（模型的偏移項）。"""
    return len(HAN.findall(text))


def count(text: str) -> dict[str, int]:
    """Raw marker counts for one text / 單篇文本的標記原始計數。"""
    return {name: len(rx.findall(text)) for name, rx in _COMPILED.items()}


def find(text: str, marker: str) -> list[str]:
    """Actual matches, for eyeballing false positives / 列出實際匹配以人工檢查。"""
    if marker not in _COMPILED:
        raise KeyError(f"unknown marker: {marker!r}; known: {list(MARKERS)}")
    return _COMPILED[marker].findall(text) or [m.group(0) for m in _COMPILED[marker].finditer(text)]
