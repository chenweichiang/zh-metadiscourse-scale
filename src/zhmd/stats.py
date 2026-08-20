"""Count models used in the paper / 論文所用的計數模型.

Two things only, both with a log-length offset so that texts of different
lengths are comparable / 兩件事，皆以文本長度的對數為偏移項：

    irr()              negative binomial GLM -> incidence rate ratio
                       負二項迴歸的率比
    conditional_rr()   zero-truncated NB on texts with >0 occurrences
                       零截斷負二項，柵欄模型（hurdle）的第二段

Why zero-truncated rather than OLS on log rate / 第二段為何不用對數線性模型：
    exp(coef) from OLS on log(count/length) is a ratio of GEOMETRIC MEANS,
    not a rate ratio, and log-normal errors do not hold for counts.
    對數線性模型得到的是幾何平均比而非率比，其常態誤差假設對計數資料不成立。

Identifiability warning / 可識別性警告：
    In short texts nearly every positive count is exactly 1. After truncating
    zeros there is no variation left and conditional_rr() returns NaN.
    That is a property of the data, not a bug.
    短文本中有出現者幾乎全為一次，零截斷後無可辨識的變異，函式回傳 NaN。
    這是資料的性質，不是程式錯誤。
"""

from __future__ import annotations

import warnings

import numpy as np
import statsmodels.api as sm
from statsmodels.discrete.truncated_model import (TruncatedLFNegativeBinomialP,
                                                  TruncatedLFPoisson)
from statsmodels.stats.multitest import multipletests


def _alpha(y: np.ndarray, X: np.ndarray, offset: np.ndarray) -> float:
    """Moment estimate of the NB dispersion / 過度離散參數的動差估計。"""
    pois = sm.GLM(y, X, family=sm.families.Poisson(), offset=offset).fit()
    mu = pois.mu
    aux = ((y - mu) ** 2 - y) / mu
    return max(sm.OLS(aux, mu / mu).fit().params[0], 1e-6)


def irr(counts, group, han, *, ci: float = 0.95):
    """Incidence rate ratio of group==1 vs group==0 / 率比與其信賴區間。

    Returns (irr, lower, upper, p). group must be 0/1.
    """
    y = np.asarray(counts, float)
    g = np.asarray(group, float).reshape(-1, 1)
    off = np.log(np.asarray(han, float))
    if y.sum() == 0 or len(np.unique(g)) < 2:
        return float("nan"), float("nan"), float("nan"), float("nan")
    X = sm.add_constant(g)
    a = _alpha(y, X, off)
    m = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=a), offset=off).fit()
    z = 1.959963985 if abs(ci - 0.95) < 1e-9 else float(-sm.stats.stattools.stats.norm.ppf((1 - ci) / 2))
    c, se = float(m.params[1]), float(m.bse[1])
    return float(np.exp(c)), float(np.exp(c - z * se)), float(np.exp(c + z * se)), float(m.pvalues[1])


def occurrence_or(counts, group):
    """Hurdle stage 1: odds of the marker occurring at all / 第一段：出現與否的勝算比。"""
    y = (np.asarray(counts, float) > 0).astype(float)
    g = np.asarray(group, float).reshape(-1, 1)
    if len(np.unique(y)) < 2 or len(np.unique(g)) < 2:
        return float("nan"), float("nan")
    m = sm.GLM(y, sm.add_constant(g), family=sm.families.Binomial()).fit()
    return float(np.exp(m.params[1])), float(m.pvalues[1])


def conditional_rr(counts, group, han, *, with_model: bool = False,
                   fallback_poisson: bool = False):
    """Hurdle stage 2: rate ratio among texts with >0 / 第二段：有出現者的條件率比。

    Returns (rate_ratio, p), or (rate_ratio, p, model_used) when with_model=True.

    Default is zero-truncated negative binomial ONLY, which is what the paper
    used; set fallback_poisson=True to fall back to a zero-truncated Poisson
    when the NB dispersion sits on its boundary. Leaving it False keeps results
    reproducible against the published numbers.
    預設只用零截斷負二項（與論文一致）；fallback_poisson=True 才在離散參數落於
    邊界時退回零截斷帕松。維持預設值方可重現論文數字。

    Returns NaN when the positive counts carry no variation (e.g. every text
    that uses the marker uses it exactly once) — the conditional rate is then
    genuinely unidentifiable, not merely hard to fit.
    有出現者的計數若無變異（例如全部恰好出現一次），條件率在統計上無法識別，回傳 NaN。
    """
    y = np.asarray(counts, float)
    g = np.asarray(group, float)
    h = np.asarray(han, float)
    pos = y > 0
    y, g, h = y[pos], g[pos], h[pos]

    def _out(rr, p, model):
        return (rr, p, model) if with_model else (rr, p)

    # 兩組都要有有出現者，計數也要有變異，否則條件率無法識別
    # both groups need positives and the counts need variation, else unidentifiable
    if len(y) < 8 or len(np.unique(g)) < 2 or len(np.unique(y)) < 2:
        return _out(float("nan"), float("nan"), "unidentifiable")
    X = sm.add_constant(g.reshape(-1, 1))
    off = np.log(h)

    models = [(TruncatedLFNegativeBinomialP, "zt-negbin")]
    if fallback_poisson:
        models.append((TruncatedLFPoisson, "zt-poisson"))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for cls, name in models:
            for method in ("bfgs", "nm", "lbfgs"):
                try:
                    r = cls(y, X, offset=off, truncation=0).fit(
                        method=method, maxiter=3000, disp=0)
                    c, p = float(r.params[1]), float(r.pvalues[1])
                    if np.isfinite(c) and np.isfinite(p) and abs(c) < 20:
                        return _out(float(np.exp(c)), p, name)
                except Exception:
                    continue
    return _out(float("nan"), float("nan"), "unidentifiable")


def single_occurrence_share(counts) -> float:
    """Share of positive texts whose count is exactly 1 / 有出現者中僅出現一次的比例。

    The higher this is, the less density information the texts carry.
    比例越高，密度資訊越少，第二段越估不出來。
    """
    y = np.asarray(counts, float)
    pos = y[y > 0]
    return float("nan") if len(pos) == 0 else float((pos == 1).sum() / len(pos))


def bh(pvalues):
    """Benjamini-Hochberg FDR / 偽發現率校正（台灣官方譯名：偽發現率）。"""
    p = np.asarray(pvalues, float)
    ok = np.isfinite(p)
    q = np.full_like(p, np.nan)
    if ok.sum():
        q[ok] = multipletests(p[ok], method="fdr_bh")[1]
    return q


def bf01_bic(counts, group, han) -> float:
    """BIC-approximated Bayes factor for the null / 以 BIC 近似的貝氏因子（Wagenmakers, 2007）。

    BF01 > 3 supports "no difference"; 1/3 to 3 means the evidence decides nothing.
    BF01 > 3 支持無差異；介於 1/3 與 3 之間表示證據不足以支持任何一方。
    """
    y = np.asarray(counts, float)
    g = np.asarray(group, float).reshape(-1, 1)
    off = np.log(np.asarray(han, float))
    n = len(y)
    if y.sum() == 0:
        return float("nan")

    def bic(X):
        a = _alpha(y, X, off)
        m = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=a), offset=off).fit()
        return -2 * m.llf + X.shape[1] * np.log(n)

    return float(np.exp((bic(sm.add_constant(g)) - bic(np.ones((n, 1)))) / 2))
