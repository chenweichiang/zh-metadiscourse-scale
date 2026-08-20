import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from zhmd import count, han_length, profile, stats  # noqa: E402
from zhmd.markers import INTERACTIVE_MARKERS, MARKERS  # noqa: E402


def test_markers_cover_ten_categories():
    assert len(MARKERS) == 10
    assert len(INTERACTIVE_MARKERS) == 6
    assert "虛假範圍" not in MARKERS, "剔除的標記不應復活 / dropped marker must stay out"


def test_counting_is_exact():
    t = "本研究不僅檢驗指標，也處理邊界，這並非分類問題，而是測量問題。綜上所述，可能仍有誤差。"
    c = count(t)
    assert c["累加轉折"] == 1 and c["對比重述"] == 1
    assert c["框架標記"] == 1 and c["模糊限制"] == 1 and c["自稱"] == 1
    assert han_length(t) == len([x for x in t if "一" <= x <= "鿿"])


def test_em_dash_only_counts_real_dashes():
    assert count("這是插入——說明")["語碼註解"] == 1
    assert count("這是連字-號")["語碼註解"] == 0


def test_profile_normalises_to_15k():
    t = "本研究" * 500                      # 1500 漢字, 500 self-mentions
    r = profile(t)
    assert r["han"] == 1500
    assert r["per15k"]["自稱"] == pytest.approx(5000.0)


def test_profile_rejects_non_chinese():
    with pytest.raises(ValueError):
        profile("no chinese here at all")


def test_irr_recovers_known_ratio():
    rng = np.random.default_rng(7)
    han = np.full(120, 12000.0)
    g = np.r_[np.zeros(60), np.ones(60)]
    y = np.r_[rng.negative_binomial(6, 6 / (6 + 3), 60),
              rng.negative_binomial(6, 6 / (6 + 15), 60)].astype(float)
    r, lo, hi, p = stats.irr(y, g, han)
    assert 3.0 < r < 7.0 and lo < r < hi and p < 0.01


def test_conditional_rr_is_nan_when_all_positives_equal():
    """短文本全為一次時必須回傳 NaN，不能硬給數字。"""
    y = np.r_[np.zeros(30), np.ones(30)]
    g = np.r_[np.zeros(30), np.ones(30)]
    rr, p, model = stats.conditional_rr(y, g, np.full(60, 300.0),
                                        with_model=True, fallback_poisson=True)
    assert np.isnan(rr) and model == "unidentifiable"


def test_single_occurrence_share():
    assert stats.single_occurrence_share([0, 1, 1, 1]) == pytest.approx(1.0)
    assert stats.single_occurrence_share([0, 1, 2, 3, 4]) == pytest.approx(0.25)


def test_bh_keeps_order_and_ignores_nan():
    q = stats.bh([0.001, 0.04, np.nan, 0.9])
    assert q[0] < q[1] < q[3] and np.isnan(q[2])


def test_bf01_supports_null_when_groups_are_identical():
    rng = np.random.default_rng(3)
    han = np.full(120, 12000.0)
    g = np.r_[np.zeros(60), np.ones(60)]
    y = rng.negative_binomial(6, 6 / (6 + 5), 120).astype(float)
    assert stats.bf01_bic(y, g, han) > 3.0


def test_reference_table_matches_paper():
    ref = profile("本研究")["reference"]
    assert ref["累加轉折"]["irr_machine_vs_human"] == pytest.approx(8.22)
    assert ref["累加轉折"]["loo_robust"] == "yes"
    assert ref["框架標記"]["loo_robust"] == "no"
    assert ref["模糊限制"]["bf01"] == pytest.approx(1.65)
