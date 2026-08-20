"""最小示範 / Minimal demo：跑一段文字，看它落在參考分布的哪裡。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from zhmd import profile  # noqa: E402

SAMPLE = (
    "本研究不僅檢驗了指標的區辨力，也處理了它的失效條件，在生成式工具普及的脈絡下，"
    "有研究指出讀者往往能指出某段文字像是機器所寫，卻難以說明依據。綜上所述，"
    "這個判斷可能仍需要更細緻的測量，值得注意的是，短文本所能承載的資訊至關重要地有限。"
)

if __name__ == "__main__":
    r = profile(SAMPLE)
    print(f"漢字 {r['han']}｜引導式合計 {r['interactive_total']:.1f} / 15,000 漢字")
    for k, v in r["per15k"].items():
        if v:
            print(f"  {k:<6}{r['counts'][k]:>3} 次 → {v:>7.1f} / 15k")
    print("\n⚠️ 這段只有百餘漢字，密度資訊幾乎不存在，只能讀『有沒有用』。")
    print("⚠️ Barely 150 characters: density is not measurable, read occurrence only.")
