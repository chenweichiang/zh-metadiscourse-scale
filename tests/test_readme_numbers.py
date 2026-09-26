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

#: README〈十條標記〉表格「率比：本機模型」欄與證據強度欄所引的貝氏因子。
#: 態度標記在本機模型文本零次出現，表格寫「—（零次）」，另由 test_attitude_zero_in_local 鎖住。
README_IRR = {"累加轉折": 8.22, "視角框架": 6.79, "引據標記": 6.71, "語碼註解": 4.29,
              "對比重述": 3.40, "框架標記": 2.62, "強調語": 0.62,
              "模糊限制": 0.67, "自稱": 1.00}
README_BF01 = {"強調語": 8.96, "模糊限制": 1.65, "自稱": 14.76}
#: 同表「率比：含商用模型」欄，以及 README 文中所引的含商用 BF01
README_IRR_ALL = {"累加轉折": 6.32, "視角框架": 5.39, "引據標記": 6.56, "語碼註解": 4.44,
                  "對比重述": 4.94, "框架標記": 1.52, "強調語": 0.50, "態度標記": 4.29,
                  "模糊限制": 0.99, "自稱": 0.83}
README_BF01_ALL = {"強調語": 3.28, "模糊限制": 13.36, "自稱": 9.89}
#: 〈為什麼不做偵測器〉其二：對比重述各模型對人類基線（全文長度）
README_CONTRAST_BY_MODEL = {"gpt-oss-120b": 1.06, "gpt-5-mini": 1.37, "gpt-5-1": 8.18}
#: 〈為什麼不做偵測器〉其三：翻譯對本機模型中文原生文本
README_TRANSLATION = {"n": 15, "語碼註解": 4.30, "對比重述": 2.94, "n_abstracts": 42}
#: README 表格標為「強，留一來源穩健」的三條
README_ROBUST = {"累加轉折", "視角框架", "引據標記"}
#: README〈怎麼讀這些數字〉：三百漢字時僅出現一次的比例
README_SHARE_300 = {"累加轉折": 95.2, "對比重述": 100.0, "視角框架": 100.0}
#: 同段：全文層級降至 38.4% 至 67.3%（對應上面三條標記）
README_SHARE_FULL_RANGE = (38.4, 67.3)

NOT_REPRODUCIBLE = {
    "作者句長 114.8 漢字、期刊中位數 2.1 倍、第 100 百分位、句長比值 0.79":
        "作者既有著作與人類期刊原文都不在 repo，也沒有計算句長的程式；README 已註明無法在此重算。",
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

@pytest.mark.parametrize("marker", list(README_IRR))
def test_readme_irr(table, marker):
    assert abs(table[marker]["irr"] - README_IRR[marker]) <= TOL_2DP


def test_attitude_zero_in_local(counts, table):
    """態度標記在本機模型 48 篇零次，率比 0.00 是發散的估計（區間 [0, ∞]），README 不寫成數字。"""
    local = counts[counts.set == rr.MACHINE]
    assert local[rr.COLUMN["態度標記"]].sum() == 0
    assert counts[counts.set == rr.HUMAN][rr.COLUMN["態度標記"]].sum() > 0
    assert table["態度標記"]["irr"] < 0.005 and not math.isfinite(table["態度標記"]["hi"])


@pytest.fixture(scope="module")
def table_all(counts):
    return rr.main_table(counts, rr.machine_all(counts))


@pytest.mark.parametrize("marker", list(MARKERS))
def test_readme_irr_with_commercial(table_all, marker):
    assert abs(table_all[marker]["irr"] - README_IRR_ALL[marker]) <= TOL_2DP


@pytest.mark.parametrize("marker", list(README_BF01_ALL))
def test_readme_bf01_with_commercial(table_all, marker):
    assert abs(table_all[marker]["bf01"] - README_BF01_ALL[marker]) <= TOL_2DP


def test_commercial_changes_three_conclusions(table, table_all):
    """README 表下說明：納入商用模型後，態度、框架、模糊三條的結論改變，其餘同側。"""
    assert table_all["態度標記"]["q"] < 0.05                                   # 零次 → 顯著偏高
    assert table["框架標記"]["q"] < 0.05 <= table_all["框架標記"]["q"]           # 顯著 → 不顯著
    assert 1 / 3 < table["模糊限制"]["bf01"] < 3 < table_all["模糊限制"]["bf01"]  # 不足 → 支持無差異
    for k in ("自稱", "強調語"):
        assert table[k]["bf01"] > 3 and table_all[k]["bf01"] > 3
    for k in ("累加轉折", "視角框架", "引據標記", "語碼註解", "對比重述"):
        assert table[k]["q"] < 0.05 and table_all[k]["q"] < 0.05


def test_contrast_by_model(counts):
    """其二：對比重述在七個模型之間 1.06（gpt-oss-120b）至 8.18（gpt-5-1），gpt-5-mini 1.37。"""
    got = rr.irr_by_model(counts, "對比重述")
    assert len(got) == 7
    for m, v in README_CONTRAST_BY_MODEL.items():
        assert abs(got[m] - v) <= TOL_2DP, m
    assert min(got, key=got.get) == "gpt-oss-120b" and max(got, key=got.get) == "gpt-5-1"


def test_translation_vs_local(counts):
    """其三：論文段落 15 篇對本機模型中文原生文本 4.30／2.94；摘要 42 篇兩者都不顯著。"""
    got = rr.translation_vs_local(counts)
    para, abst = got["paragraphs"], got["abstracts"]
    assert para["n"] == README_TRANSLATION["n"] and abst["n"] == README_TRANSLATION["n_abstracts"]
    for k in ("語碼註解", "對比重述"):
        assert abs(para[k][0] - README_TRANSLATION[k]) <= TOL_2DP, k
        assert para[k][3] < 0.05 <= abst[k][3], k


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
    """README（本機模型）：自稱、強調語支持無差異（>3），模糊限制證據不足（1/3–3）。"""
    for k in ("自稱", "強調語"):
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


def test_cli_interactive_reference_totals(counts):
    """cli.py 印出的 7.5／16.6／39.0 是六條引導式標記 per15k 平均的加總（先加總再四捨五入）。
    機器組未四捨五入加總 38.95 → 39.0；把 reference.csv 已四捨五入的六個值相加會得 38.9，
    兩者差在進位順序，cli.py 與論文的 39.0 是對的。"""
    m = rr.per15k_means(counts)
    total = {g: round(sum(v[g] for v in m.values()), 1)
             for g in ("human_2018_2022", "human_2024_2026", "machine")}
    assert total == {"human_2018_2022": 7.5, "human_2024_2026": 16.6, "machine": 39.0}
    src = (ROOT / "src" / "zhmd" / "cli.py").read_text(encoding="utf-8")
    assert "人類 2018–22: 7.5" in src and "人類 2024–26: 16.6" in src and "機器 machine: 39.0" in src


@pytest.mark.parametrize("claim", list(NOT_REPRODUCIBLE))
def test_not_reproducible_from_repo(claim):
    pytest.skip(f"無法只用 repo 資料重算：{NOT_REPRODUCIBLE[claim]}")
