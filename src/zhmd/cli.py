"""Command line entry / 命令列介面：zhmd <file>…"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .markers import INTERACTIONAL_MARKERS, INTERACTIVE_MARKERS, MARKERS, find
from .profile import PER, profile


def _bar(value: float, lo: float, hi: float, width: int = 24) -> str:
    if hi <= lo:
        return ""
    pos = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    i = int(round(pos * (width - 1)))
    return "".join("▲" if j == i else "·" for j in range(width))


def report(path: Path, show_matches: bool) -> None:
    text = path.read_text("utf-8", errors="ignore")
    r = profile(text)
    ref = r["reference"]
    print(f"\n=== {path.name} ===")
    print(f"漢字數 Chinese characters: {r['han']:,}")
    if r["han"] < 3000:
        print("⚠️  短文本：密度資訊有限，僅「有沒有用」可讀，見 README 的長度效應一節。")
        print("⚠️  Short text: density is barely measurable here; read occurrence only.")
    print(f"\n引導式標記合計 interactive total: {r['interactive_total']:.1f} / {PER:,} 漢字")
    print(f"  參考 reference — 人類 2018–22: 7.5 ｜ 人類 2024–26: 16.6 ｜ 機器 machine: 39.0")
    print(f"  {_bar(r['interactive_total'], 0, 39.0)}  (0 ——— 39.0)")

    print(f"\n{'標記 marker':<12}{'次數':>5}{'/15k':>8}{'人類18-22':>10}{'機器':>8}   證據 evidence")
    for group, label in ((INTERACTIVE_MARKERS, "interactive 引導式"),
                         (INTERACTIONAL_MARKERS, "interactional 互動式")):
        print(f"-- {label}")
        for k in group:
            m = ref.get(k, {})
            h = m.get("per15k_human_2018_2022")
            mc = m.get("per15k_machine")
            ev = ""
            if m.get("loo_robust") == "yes":
                ev = "強證據 strong"
            elif m.get("category") == "interactive":
                ev = "中等，對來源敏感 moderate"
            elif isinstance(m.get("bf01"), float):
                bf = m["bf01"]
                ev = ("支持無差異 null supported" if bf > 3
                      else "證據不足 inconclusive" if bf > 1 / 3 else "")
            print(f"{k:<12}{r['counts'][k]:>5}{r['per15k'][k]:>8.1f}"
                  f"{('' if h in (None,'') else f'{h:>10.1f}')}"
                  f"{('' if mc in (None,'') else f'{mc:>8.1f}')}   {ev}")
    if show_matches:
        print("\n--- 實際匹配 actual matches（人工判讀用；正規表示式分不出使用與提及）---")
        for k in MARKERS:
            hits = find(text, k)
            if hits:
                print(f"{k}: " + "、".join(h[:24] for h in hits[:6]) + (" …" if len(hits) > 6 else ""))
    print("\n這是描述性量尺，不是偵測器；任何以個人為單位的判定都不成立，見 README。")
    print("A descriptive scale, not a detector. Do not use it to judge authorship.\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="zhmd",
        description="中文學術寫作的後設論述標記量尺 / Metadiscourse scale for Chinese academic writing")
    ap.add_argument("files", nargs="+", type=Path, help="UTF-8 文字檔 / UTF-8 text files")
    ap.add_argument("--matches", action="store_true",
                    help="列出實際匹配 / list the actual matches for manual checking")
    a = ap.parse_args(argv)
    missing = [f for f in a.files if not f.is_file()]
    if missing:
        print("找不到檔案 / file not found: " + ", ".join(map(str, missing)), file=sys.stderr)
        return 2
    for f in a.files:
        report(f, a.matches)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
