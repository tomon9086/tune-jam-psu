#!/usr/bin/env python3
"""CC ループのシミュレーション結果を合否判定する（VER-07a）。

使い方：python check.py [名前 ...]   （gen.py のあとに ngspice -b 名前.cir を回しておく）

合格の条件（Vset 5V、Iset 1A、0.6〜1.6ms に負荷 2.5A 相当）：
- 負荷をつなぐ前（0.4〜0.6ms）：出力 5V ± 2%
- CC に入った直後：CC アンプが 10µs 以内に反応し（出力が 1.5V を超える）、電流が Iset × 1.1 以下に
  戻るまで 300µs 以内。出力コンデンサ（シャントの手前）の放電は止められないので、直後の電流の最大は
  負荷の要求（2.5A）に近くなる。これは判定せず、表示だけする
- CC 中（1.0〜1.6ms）：電流の平均が 1A ± 10%、揺れ（最大 − 最小）が 0.6A 以下
- 負荷を外したあと（1.6〜2.4ms）：出力の最大が 5V の +5% 以下（VAR-12）、2.2〜2.4ms の平均が 5V ± 2%
"""
import sys

VSET, ISET = 5.0, 1.0
K = 20 * 0.0333          # INA180A1 の出力（V）→ 電流（A）
BIN = 1e-6


def load(name):
    """1µs ごとに、出力電圧・電流・CC アンプ出力の最小と最大をまとめる。"""
    bins = {}
    for line in open(f"{name}.txt"):
        r = line.split()
        if len(r) < 8:
            continue
        t = float(r[0])
        v, i, cc = float(r[1]), float(r[5]) / K, float(r[7])
        b = bins.setdefault(int(t / BIN), [v, v, i, i, cc, cc, 0.0, 0, 0.0])
        b[0], b[1] = min(b[0], v), max(b[1], v)
        b[2], b[3] = min(b[2], i), max(b[3], i)
        b[4], b[5] = min(b[4], cc), max(b[5], cc)
        b[6] += v; b[7] += 1; b[8] += i
    return bins


def main():
    names = sys.argv[1:] or ["a_slow", "b_mid", "c_fast", "d_mid_h4n7", "e_mid_h10n", "f_fast_h10n"]
    ok_all = True
    for n in names:
        try:
            bins = load(n)
        except FileNotFoundError:
            print(f"  NG  {n}: 結果がない"); ok_all = False; continue
        last = max(bins) * BIN
        if last < 2.39e-3:
            print(f"  NG  {n}: 計算が {last * 1e3:.2f}ms で止まった"); ok_all = False; continue
        rng = lambda a, b: [bins[k] for k in range(int(a / BIN), int(b / BIN)) if k in bins]
        avg_v = lambda a, b: sum(x[6] for x in rng(a, b)) / sum(x[7] for x in rng(a, b))
        avg_i = lambda a, b: sum(x[8] for x in rng(a, b)) / sum(x[7] for x in rng(a, b))
        v_pre = avg_v(0.4e-3, 0.6e-3)
        cc_win = rng(1.0e-3, 1.6e-3)
        i_avg = avg_i(1.0e-3, 1.6e-3)
        i_pp = max(x[3] for x in cc_win) - min(x[2] for x in cc_win)
        i_pk = max(x[3] for x in rng(0.6e-3, 1.0e-3))
        t_resp = next((k * BIN for k in range(int(0.6e-3 / BIN), int(1.0e-3 / BIN)) if k in bins and bins[k][5] > 1.5), 1) - 0.6e-3
        imax = [bins[k][3] if k in bins else 0 for k in range(int(0.6e-3 / BIN), int(1.6e-3 / BIN))]
        t_settle = next((j * BIN for j in range(len(imax)) if j * BIN >= 50e-6 and max(imax[j:j + 50]) <= 1.1 * ISET), 1)
        v_ov = max(x[1] for x in rng(1.6e-3, 2.4e-3))
        v_end = avg_v(2.2e-3, 2.4e-3)
        checks = {
            f"前 {v_pre:.3f}V": abs(v_pre - VSET) <= 0.02 * VSET,
            f"反応 {t_resp * 1e6:.1f}µs": t_resp <= 10e-6,
            f"Iset×1.1 以下まで {t_settle * 1e6:.0f}µs（最大 {i_pk:.2f}A）": t_settle <= 300e-6,
            f"CC 平均 {i_avg:.3f}A": abs(i_avg - ISET) <= 0.1 * ISET,
            f"CC 揺れ {i_pp:.3f}A": i_pp <= 0.6,
            f"戻りの最大 {v_ov:.3f}V": v_ov <= 1.05 * VSET,
            f"戻り {v_end:.3f}V": abs(v_end - VSET) <= 0.02 * VSET,
        }
        good = all(checks.values())
        ok_all &= good
        print(f"  {'OK' if good else 'NG'}  {n}: " + "、".join(f"{k}{'' if v else '（NG）'}" for k, v in checks.items()))
    print("CC ループ：" + ("合格" if ok_all else "不合格あり"))
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
