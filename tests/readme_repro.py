"""用 repo 內的 data/ 與 src/zhmd/ 重算 README 所列的數字。

Recompute the numbers stated in README.md from data/ and src/zhmd/ only.
測試與人工比對共用這裡的計算；直接執行可印出對照表：

    python tests/readme_repro.py

資料切分（v1.0.1 起寫進 README）：
    人類基線   human_2018_2022（122 篇）
    本機模型   machine_local（三個本機開放權重模型 × 兩種提示 × 八題，48 篇）
    含商用模型 machine_local＋machine_commercial（四個商用模型各 16 篇，共 112 篇）
    留一來源   依 machine_local 的 model 欄逐一剔除
    300 漢字   machine_local 各篇取前 300 個漢字後重新計數
    翻譯       translation 依檔名分兩批，各自對 machine_local 比：
               T_＝論文段落（gemma4，15 篇）、T2_＝arXiv 摘要（42 篇）
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "src"))

from zhmd import count, stats  # noqa: E402
from zhmd.markers import HAN, INTERACTIVE_MARKERS, MARKERS  # noqa: E402

#: marker_counts.csv 的英文欄名 / column names in data/marker_counts.csv
COLUMN = {
    "累加轉折": "additive_transition",
    "對比重述": "contrastive_restatement",
    "框架標記": "frame_marker",
    "語碼註解": "code_gloss",
    "引據標記": "evidential",
    "視角框架": "perspective_frame",
    "強調語": "booster",
    "態度標記": "attitude_marker",
    "模糊限制": "hedge",
    "自稱": "self_mention",
}
assert set(COLUMN) == set(MARKERS)

HUMAN = "human_2018_2022"
MACHINE = "machine_local"
COMMERCIAL = "machine_commercial"


def load_counts() -> pd.DataFrame:
    return pd.read_csv(DATA / "marker_counts.csv")


def _pair(d: pd.DataFrame, machine: pd.DataFrame | None = None) -> pd.DataFrame:
    h = d[d.set == HUMAN].assign(g=0)
    m = (d[d.set == MACHINE] if machine is None else machine).assign(g=1)
    return pd.concat([h, m], ignore_index=True)


def machine_all(d: pd.DataFrame) -> pd.DataFrame:
    """本機＋商用模型，README 表格的「含商用模型」欄。"""
    return d[d.set.isin([MACHINE, COMMERCIAL])]


def main_table(d: pd.DataFrame, machine: pd.DataFrame | None = None) -> dict[str, dict[str, float]]:
    """README 表格與 reference.csv 的率比、信賴區間、q 與 BF01。

    machine 省略時為本機模型（README 主欄與 reference.csv），傳入 machine_all(d) 為含商用模型欄。"""
    x = _pair(d, machine)
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for k, col in COLUMN.items():
            r, lo, hi, p = stats.irr(x[col], x.g, x.han_chars)
            out[k] = {"irr": r, "lo": lo, "hi": hi, "p": p,
                      "bf01": stats.bf01_bic(x[col], x.g, x.han_chars)}
    q = stats.bh([out[k]["p"] for k in COLUMN])
    for k, qq in zip(COLUMN, q):
        out[k]["q"] = float(qq)
    return out


def per15k_means(d: pd.DataFrame) -> dict[str, dict[str, float]]:
    """每 15,000 漢字的平均率（逐篇換算後取平均），對應 reference.csv 的 per15k_* 欄。"""
    groups = {"human_2018_2022": d[d.set == "human_2018_2022"],
              "human_2024_2026": d[d.set == "human_2024_2026"],
              "machine": d[d.set == MACHINE]}
    return {k: {g: float((x[COLUMN[k]] / x.han_chars * 15000).mean()) for g, x in groups.items()}
            for k in INTERACTIVE_MARKERS}


def loo_pvalues(d: pd.DataFrame) -> dict[str, dict[str, float]]:
    """留一來源：每次剔除一個本機模型後的率比 p 值。"""
    m = d[d.set == MACHINE]
    out: dict[str, dict[str, float]] = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for k in INTERACTIVE_MARKERS:
            out[k] = {}
            for model in sorted(m.model.unique()):
                x = _pair(d, m[m.model != model])
                out[k][model] = stats.irr(x[COLUMN[k]], x.g, x.han_chars)[3]
    return out


def irr_by_model(d: pd.DataFrame, marker: str) -> dict[str, float]:
    """七個模型（本機三個、商用四個）各自對人類基線的率比，全文長度。"""
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for s in (MACHINE, COMMERCIAL):
            for model, g in d[d.set == s].groupby("model"):
                x = _pair(d, g)
                out[model] = stats.irr(x[COLUMN[marker]], x.g, x.han_chars)[0]
    return out


def translation_vs_local(d: pd.DataFrame) -> dict[str, dict]:
    """翻譯兩批各自對本機模型中文原生文本（machine_local，不是人類）的率比。

    比較對象與論文相同：翻譯任務相對同一批模型自己寫中文，兩批長度差很多，合併會稀釋訊號。"""
    t = d[d.set == "translation"]
    local = d[d.set == MACHINE].assign(g=0)
    out = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for name, prefix in (("paragraphs", "T_"), ("abstracts", "T2_")):
            b = t[t.text_id.str.startswith(prefix)].assign(g=1)
            x = pd.concat([local, b], ignore_index=True)
            out[name] = {"n": len(b)}
            for k in ("語碼註解", "對比重述"):
                out[name][k] = stats.irr(x[COLUMN[k]], x.g, x.han_chars)
    return out


def single_share_full(d: pd.DataFrame) -> dict[str, float]:
    """全文層級：有出現者中僅出現一次的比例（人類基線與機器組合併）。"""
    x = _pair(d)
    return {k: stats.single_occurrence_share(x[COLUMN[k]]) for k in MARKERS}


def first_han(text: str, n: int) -> str:
    """截到第 n 個漢字為止 / cut the text right after its n-th Chinese character."""
    for i, mt in enumerate(HAN.finditer(text), 1):
        if i == n:
            return text[:mt.end()]
    return text


def single_share_truncated(d: pd.DataFrame, n: int = 300) -> dict[str, tuple[float, int]]:
    """機器組各篇取前 n 個漢字後，僅出現一次的比例與有出現的篇數。"""
    ids = d[d.set == MACHINE].text_id
    rows = pd.DataFrame([count(first_han((DATA / "machine_texts" / f"{i}.txt")
                                         .read_text("utf-8"), n)) for i in ids])
    return {k: (stats.single_occurrence_share(rows[k]), int((rows[k] > 0).sum()))
            for k in MARKERS}


if __name__ == "__main__":
    d = load_counts()
    print("率比 machine_local vs human_2018_2022")
    for k, v in main_table(d).items():
        print(f"  {k:<6}IRR {v['irr']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}]"
              f"  q {v['q']:.4f}  BF01 {v['bf01']:.2f}")
    print("率比 含商用模型（machine_local + machine_commercial）vs human_2018_2022")
    for k, v in main_table(d, machine_all(d)).items():
        print(f"  {k:<6}IRR {v['irr']:.2f} [{v['lo']:.2f}, {v['hi']:.2f}]"
              f"  q {v['q']:.4f}  BF01 {v['bf01']:.2f}")
    print("對比重述：各模型對人類基線（全文）")
    for m, r in sorted(irr_by_model(d, "對比重述").items(), key=lambda kv: kv[1]):
        print(f"  {m:<14}{r:.2f}")
    print("翻譯對本機模型中文原生文本")
    for name, v in translation_vs_local(d).items():
        print(f"  {name:<11}n={v['n']:<3}" + "  ".join(
            f"{k} {v[k][0]:.2f} (p {v[k][3]:.3f})" for k in ("語碼註解", "對比重述")))
    print("每 15k 漢字平均率")
    for k, v in per15k_means(d).items():
        print(f"  {k:<6}" + "  ".join(f"{g} {x:.2f}" for g, x in v.items()))
    print("留一來源 p 值")
    for k, v in loo_pvalues(d).items():
        print(f"  {k:<6}" + "  ".join(f"-{m} {p:.4f}" for m, p in v.items()))
    print("僅出現一次的比例：全文 / 前 300 漢字（有出現篇數）")
    full, short = single_share_full(d), single_share_truncated(d)
    for k in MARKERS:
        s, n = short[k]
        print(f"  {k:<6}{full[k] * 100:6.1f}%  {s * 100:6.1f}% (n={n})")
