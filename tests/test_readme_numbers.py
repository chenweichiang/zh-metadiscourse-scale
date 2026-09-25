"""回歸測試：用 data/ 重跑，結果必須與 README.md 及 reference.csv 的數字一致。

Regression test: rerunning on data/ must reproduce the numbers in README.md.

容許誤差 / tolerances
    README 與 reference.csv 的數字都是四捨五入後的值，因此容許誤差取「最後一位的一半」，
    再加上 1e-3 個最後一位的數值餘裕（跨 numpy / statsmodels 版本的浮點差異）：
        率比、信賴區間、BF01（兩位小數）   |重跑 - 表列| <= 0.005 + 1e-5
        q 值（四位小數）                  |重跑 - 表列| <= 0.00005 + 1e-7
        每 15k 漢字平均率（一位小數）      |重跑 - 表列| <= 0.05 + 1e-4
        百分比（一位小數，以 % 計）        |重跑 - 表列| <= 0.05 + 1e-4
    也就是說，重跑值四捨五入到表列的位數後必須完全相同。
    計數（data/marker_counts.csv 與 machine_texts/ 重新計數）不容許任何誤差。

README 裡無法只靠 repo 內資料重算的數字列在 NOT_REPRODUCIBLE，以 skip 標示，理由寫在其中。
"""
import csv
import math
from pathlib import Path

import pytest

import readme_repro as rr
from zhmd import count, han_length
from zhmd.markers import INTERACTIVE_MARKERS, MARKERS

ROOT = Path(__file__).resolve().parents[1]

TOL_2DP = 0.005 + 1e-5
TOL_4DP = 0.00005 + 1e-7
TOL_1DP = 0.05 + 1e-4

#: README〈十條標記〉表格的「機器對人類率比」與證據強度欄所引的貝氏因子
README_IRR = {"累加轉折": 8.22, "視角框架": 6.79, "引據標記": 6.71, "語碼註解": 4.29,
              "對比重述": 3.40, "框架標記": 2.62, "強調語": 0.62, "態度標記": 0.00,
              "模糊限制": 0.67, "自稱": 1.00}
README_BF01 = {"強調語": 8.96, "態度標記": 3.47, "模糊限制": 1.65, "自稱": 14.76}
#: README 表格標為「強，留一來源穩健」的三條
README_ROBUST = {"累加轉折", "視角框架", "引據標記"}
#: README〈怎麼讀這些數字〉：三百漢字時僅出現一次的比例
README_SHARE_300 = {"累加轉折": 95.2, "對比重述": 100.0, "視角框架": 100.0}
#: 同段：全文層級降至 38.4% 至 67.3%（對應上面三條標記）
README_SHARE_FULL_RANGE = (38.4, 67.3)

NOT_REPRODUCIBLE = {
    "對比重述在大型商用模型 11.85 倍、小型模型 1.45 倍":
        "marker_counts.csv 裡任何單一商用或本機模型對 human_2018_2022 的率比都不是這兩個值"
        "（商用 gpt-5-1 8.18、opus-5 6.66、sonnet-5 5.97、gpt-5-mini 1.37；本機 gpt-oss-120b 1.06、"
        "gpt-oss 1.96、gemma4 6.71），README 也未說明模型分組方式。",
    "英譯中樣本語碼註解 4.30 倍、對比重述 2.94 倍":
        "README 說是與「論文段落長度相當」的比較；repo 不含長度相當的人類段落，"
        "translation 組對全文人類基線重算為 7.92 與 4.73。",
    "作者句長落在第 100 百分位、個體差異 2.1 倍、句長比值 0.79":
        "repo 沒有句長資料、作者既有著作，也沒有計算句長的程式。",
}


def _reference():
    with (ROOT / "src" / "zhmd" / "reference.csv").open(encoding="utf-8") as fh:
        return {r["marker"]: r for r in csv.DictReader(fh)}


@pytest.fixture(scope="module")
def counts():
    return rr.load_counts()


@pytest.fixture(scope="module")
def table(counts):
    return rr.main_table(counts)


# ---- 資料本身 -------------------------------------------------------------

def test_data_readme_set_sizes(counts):
    """data/README.md 的篇數：385 篇，各組 n 與表列相同。"""
    assert len(counts) == 385
    assert counts.set.value_counts().to_dict() == {
        "human_2018_2022": 122, "human_2024_2026": 62, "machine_local": 48,
        "machine_commercial": 64, "temperature_variant": 32, "translation": 57}
    assert counts[counts.set == "machine_local"].model.nunique() == 3
    assert counts[counts.set == "machine_commercial"].groupby("model").size().eq(16).all()
    assert len(list((rr.DATA / "machine_texts").glob("*.txt"))) == 201


def test_marker_definitions_csv_matches_code():
    with (rr.DATA / "marker_definitions.csv").open(encoding="utf-8") as fh:
        defs = {r["marker"]: r["regex"] for r in csv.DictReader(fh)}
    assert {k: defs[v] for k, v in rr.COLUMN.items()} == {k: v[0] for k, v in MARKERS.items()}


def test_machine_texts_recount_exactly(counts):
    """重新計數 201 篇機器與翻譯文本，必須與 marker_counts.csv 完全相同。"""
    rows = counts.set_index("text_id")
    for f in sorted((rr.DATA / "machine_texts").glob("*.txt")):
        text = f.read_text("utf-8")
        row = rows.loc[f.stem]
        assert han_length(text) == row.han_chars, f.stem
        got = count(text)
        assert {k: got[k] for k in MARKERS} == {k: row[c] for k, c in rr.COLUMN.items()}, f.stem


# ---- README 表格與 reference.csv ------------------------------------------

@pytest.mark.parametrize("marker", list(MARKERS))
def test_readme_irr(table, marker):
    assert abs(table[marker]["irr"] - README_IRR[marker]) <= TOL_2DP


@pytest.mark.parametrize("marker", list(README_BF01))
def test_readme_bf01(table, marker):
    assert abs(table[marker]["bf01"] - README_BF01[marker]) <= TOL_2DP


@pytest.mark.parametrize("marker", list(MARKERS))
def test_reference_csv_statistics(table, marker):
    ref = _reference()[marker]
    got = table[marker]
    assert abs(got["irr"] - float(ref["irr_machine_vs_human"])) <= TOL_2DP
    assert abs(got["q"] - float(ref["q"])) <= TOL_4DP
    assert abs(got["bf01"] - float(ref["bf01"])) <= TOL_2DP
    if ref["irr_ci_low"]:
        assert abs(got["lo"] - float(ref["irr_ci_low"])) <= TOL_2DP
        assert abs(got["hi"] - float(ref["irr_ci_high"])) <= TOL_2DP
    else:
        # 態度標記：機器組零次，區間無法估計，reference.csv 留空
        assert got["lo"] < 0.005 and not math.isfinite(got["hi"])


@pytest.mark.parametrize("marker", INTERACTIVE_MARKERS)
def test_reference_csv_per15k(counts, marker):
    ref = _reference()[marker]
    got = rr.per15k_means(counts)[marker]
    for group in ("human_2018_2022", "human_2024_2026", "machine"):
        assert abs(got[group] - float(ref[f"per15k_{group}"])) <= TOL_1DP, group


def test_evidence_strength_column(counts, table):
    """「強，留一來源穩健」三條：留一來源全部 p < .05 且 BF01 < 1/3；
    其餘三條引導式標記：至少剔除一個模型後 p >= .05。"""
    loo = rr.loo_pvalues(counts)
    ref = _reference()
    for k in INTERACTIVE_MARKERS:
        robust = all(p < 0.05 for p in loo[k].values()) and table[k]["bf01"] < 1 / 3
        assert robust == (k in README_ROBUST), (k, loo[k])
        assert (ref[k]["loo_robust"] == "yes") == (k in README_ROBUST)


def test_bf01_classification_matches_readme(table):
    """README：自稱、強調語、態度標記支持無差異（>3），模糊限制證據不足（1/3–3）。"""
    for k in ("自稱", "強調語", "態度標記"):
        assert table[k]["bf01"] > 3
    assert 1 / 3 < table["模糊限制"]["bf01"] < 3


# ---- 長度效應 ---------------------------------------------------------------

def test_single_occurrence_share_300_chars(counts):
    got = rr.single_share_truncated(counts, 300)
    for k, pct in README_SHARE_300.items():
        assert abs(got[k][0] * 100 - pct) <= TOL_1DP, k


def test_single_occurrence_share_full_text(counts):
    got = rr.single_share_full(counts)
    vals = [got[k] * 100 for k in README_SHARE_300]
    assert abs(min(vals) - README_SHARE_FULL_RANGE[0]) <= TOL_1DP
    assert abs(max(vals) - README_SHARE_FULL_RANGE[1]) <= TOL_1DP


def test_cli_interactive_reference_totals():
    """cli.py 印出的 7.5／16.6 是 reference.csv 六條引導式標記 per15k 的加總。
    機器組加總為 38.9，cli.py 寫死 39.0（見 PR 說明），這裡只鎖住兩組人類值。"""
    ref = _reference()
    total = {g: sum(float(ref[k][f"per15k_{g}"]) for k in INTERACTIVE_MARKERS)
             for g in ("human_2018_2022", "human_2024_2026", "machine")}
    assert total["human_2018_2022"] == pytest.approx(7.5)
    assert total["human_2024_2026"] == pytest.approx(16.6)
    assert total["machine"] == pytest.approx(38.9)


@pytest.mark.parametrize("claim", list(NOT_REPRODUCIBLE))
def test_not_reproducible_from_repo(claim):
    pytest.skip(f"無法只用 repo 資料重算：{NOT_REPRODUCIBLE[claim]}")
