"""冒煙測試：每支 Python 程式都能載入、執行並回傳合理的形狀，不連網。

Smoke tests for every Python file in the repo; no network access.
"""
import importlib
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

import zhmd
from zhmd import cli, markers, stats

# zhmd.profile 在套件層被同名函式遮蔽，改用 import_module 取得模組
profile_mod = importlib.import_module("zhmd.profile")

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ("本研究不僅檢驗了指標，也處理了失效條件。在生成式工具普及的脈絡下，"
          "有研究指出讀者往往能指出差異——卻難以說明依據。綜上所述，這可能仍需要更細緻的測量。")


def _env():
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    return env


# ---- src/zhmd/__init__.py ------------------------------------------------

def test_package_exports_and_version():
    for name in zhmd.__all__:
        assert hasattr(zhmd, name), name
    # Python 3.10 沒有 tomllib，直接比對 pyproject.toml 的 version 行
    m = re.search(r'^version\s*=\s*"([^"]+)"', (ROOT / "pyproject.toml").read_text("utf-8"), re.M)
    assert m and zhmd.__version__ == m.group(1)


# ---- src/zhmd/markers.py -------------------------------------------------

def test_markers_smoke():
    c = markers.count(SAMPLE)
    assert set(c) == set(markers.MARKERS) and all(isinstance(v, int) for v in c.values())
    assert markers.find(SAMPLE, "累加轉折")
    assert markers.han_length("abc 中文") == 2
    assert set(markers.INTERACTIVE_MARKERS) | set(markers.INTERACTIONAL_MARKERS) == set(markers.MARKERS)
    with pytest.raises(KeyError):
        markers.find(SAMPLE, "虛假範圍")


# ---- src/zhmd/profile.py -------------------------------------------------

def test_profile_smoke():
    r = profile_mod.profile(SAMPLE)
    assert set(r) == {"han", "counts", "per15k", "interactive_total", "reference"}
    assert r["interactive_total"] == pytest.approx(
        sum(r["per15k"][k] for k in markers.INTERACTIVE_MARKERS))
    ref = profile_mod.load_reference()
    assert set(ref) == set(markers.MARKERS)
    assert isinstance(ref["累加轉折"]["irr_machine_vs_human"], float)
    assert ref["自稱"]["per15k_machine"] == ""        # 互動式標記沒有 per15k 參考值


# ---- src/zhmd/stats.py ---------------------------------------------------

def test_stats_smoke():
    rng = np.random.default_rng(11)
    n = 80
    g = np.r_[np.zeros(n // 2), np.ones(n // 2)]
    han = rng.integers(8000, 20000, n).astype(float)
    y = rng.poisson(np.where(g == 1, 6.0, 2.0) * han / 12000).astype(float)

    r, lo, hi, p = stats.irr(y, g, han)
    assert lo < r < hi and 0 <= p <= 1
    orr, p1 = stats.occurrence_or(y, g)
    assert orr > 0 and 0 <= p1 <= 1
    crr, p2, model = stats.conditional_rr(y, g, han, with_model=True)
    assert model in ("zt-negbin", "unidentifiable")
    assert (math.isnan(crr) and model == "unidentifiable") or crr > 0
    assert 0 < stats.bf01_bic(y, g, han)
    assert 0 <= stats.single_occurrence_share(y) <= 1


def test_stats_degenerate_inputs_return_nan():
    assert all(math.isnan(v) for v in stats.irr([0, 0, 0, 0], [0, 0, 1, 1], [100] * 4))
    assert all(math.isnan(v) for v in stats.irr([1, 2, 3], [1, 1, 1], [100] * 3))
    assert all(math.isnan(v) for v in stats.occurrence_or([1, 1, 1, 1], [0, 0, 1, 1]))
    assert math.isnan(stats.single_occurrence_share([0, 0]))
    assert math.isnan(stats.bf01_bic([0, 0, 0], [0, 1, 1], [100] * 3))
    assert np.isnan(stats.bh([np.nan, np.nan])).all()


# ---- src/zhmd/cli.py -----------------------------------------------------

def test_cli_main_prints_report(tmp_path, capsys):
    f = tmp_path / "sample.txt"
    f.write_text(SAMPLE, encoding="utf-8")
    assert cli.main([str(f), "--matches"]) == 0
    out = capsys.readouterr().out
    assert "sample.txt" in out and "實際匹配" in out
    assert "不是偵測器" in out and "not a detector" in out


def test_cli_missing_file_returns_2(tmp_path, capsys):
    assert cli.main([str(tmp_path / "nope.txt")]) == 2
    assert "找不到檔案" in capsys.readouterr().err


def test_cli_on_repo_data_file(capsys):
    f = next((ROOT / "data" / "machine_texts").glob("*.txt"))
    assert cli.main([str(f)]) == 0
    assert "短文本" in capsys.readouterr().out


def test_cli_runs_as_module(tmp_path):
    f = tmp_path / "s.txt"
    f.write_text(SAMPLE, encoding="utf-8")
    p = subprocess.run([sys.executable, "-m", "zhmd.cli", str(f)], capture_output=True,
                       text=True, encoding="utf-8", env=_env(), timeout=120)
    assert p.returncode == 0, p.stderr
    assert "引導式標記合計" in p.stdout


# ---- examples/demo.py ----------------------------------------------------

def test_demo_runs():
    p = subprocess.run([sys.executable, str(ROOT / "examples" / "demo.py")], capture_output=True,
                       text=True, encoding="utf-8", env=_env(), timeout=120)
    assert p.returncode == 0, p.stderr
    assert "引導式合計" in p.stdout and "累加轉折" in p.stdout


# ---- tests/readme_repro.py -----------------------------------------------

def test_readme_repro_script_runs():
    p = subprocess.run([sys.executable, str(ROOT / "tests" / "readme_repro.py")], capture_output=True,
                       text=True, encoding="utf-8", env=_env(), timeout=300)
    assert p.returncode == 0, p.stderr
    assert "8.22" in p.stdout


def test_first_han_truncation():
    from readme_repro import first_han
    assert first_han("ab中文c字", 2) == "ab中文"
    assert first_han("中", 5) == "中"
