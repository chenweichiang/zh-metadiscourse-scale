"""Situate one text against the published reference distributions.

把一篇文本放到論文的參考分布上，回答「我落在哪個區間」。
"""

from __future__ import annotations

import csv
from importlib import resources
from typing import Any

from .markers import INTERACTIVE_MARKERS, count, han_length

PER = 15000  #: normalisation unit, one typical article / 換算單位＝一篇典型論文的長度


def load_reference() -> dict[str, dict[str, Any]]:
    """Published reference values / 論文的參考值（見 reference.csv 與 README）。"""
    with resources.files(__package__).joinpath("reference.csv").open(encoding="utf-8") as fh:
        out = {}
        for row in csv.DictReader(fh):
            out[row["marker"]] = {k: (float(v) if v not in ("", None) and k != "marker"
                                      and k not in ("category", "loo_robust") else v)
                                  for k, v in row.items()}
        return out


def profile(text: str) -> dict[str, Any]:
    """Marker profile of one text / 單篇文本的標記剖面。

    Returns raw counts, rates per 15,000 Chinese characters, the interactive
    total, and the reference values to compare against.
    回傳原始計數、每 15,000 漢字的換算值、引導式合計，以及可供對照的參考值。
    """
    n = han_length(text)
    if n == 0:
        raise ValueError("no Chinese characters found / 找不到漢字，請確認輸入是中文文本")
    raw = count(text)
    rate = {k: v / n * PER for k, v in raw.items()}
    ref = load_reference()
    return {
        "han": n,
        "counts": raw,
        "per15k": rate,
        "interactive_total": sum(rate[k] for k in INTERACTIVE_MARKERS),
        "reference": ref,
    }
