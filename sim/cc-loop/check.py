#!/usr/bin/env python3
"""CC ループのシミュレーション結果を合否判定する（VER-07a）。

使い方：python check.py [名前 ...]   （gen.py のあとに ngspice -b 名前.cir を回しておく）

合格の条件（Vset 5V、Iset 1A、0.6〜1.6ms に負荷 2.5A 相当）：
- 負荷をつなぐ前（0.4〜0.6ms）：出力 5V ± 2%
- CC 中（1.0〜1.6ms）：シャントの電流の平均が 1A ± 10%、揺れ（最大 − 最小、スイッチングのリップルを含む）が 0.6A 以下
- CC に入った直後（0.6〜1.0ms）：電流の最大が 2.0A 以下（突入を抑えられること）
- 負荷を外したあと（1.6〜2.4ms）：出力の最大が 5V の +5% 以下（VAR-12）、2.2〜2.4ms の平均が 5V ± 2%
"""
import sys

VSET, ISET = 5.0, 1.0
RSH = 0.0333


def load(name):
    t, vs, csa = [], [], []
    for line in open(f"{name}.txt"):
        r = line.split()
        if len(r) < 6:
            continue
        t.append(float(r[0])); vs.append(float(r[1])); csa.append(float(r[5]))
    return t, vs, csa


def window(t, y, a, b):
    return [y[i] for i in range(len(t)) if a <= t[i] <= b]


def main():
    names = sys.argv[1:] or ["a_slow", "b_mid", "c_fast"]
    ok_all = True
    for n in names:
        try:
            t, vs, csa = load(n)
        except FileNotFoundError:
            print(f"  NG  {n}: 結果がない"); ok_all = False; continue
        if t[-1] < 2.39e-3:
            print(f"  NG  {n}: 計算が {t[-1] * 1e3:.2f}ms で止まった"); ok_all = False; continue
        cur = [c / 20 / RSH for c in csa]   # INA180A1 の出力から電流に換算（帯域 350kHz 込み）
        v_pre = sum(window(t, vs, 0.4e-3, 0.6e-3)) / len(window(t, vs, 0.4e-3, 0.6e-3))
        i_cc = window(t, cur, 1.0e-3, 1.6e-3)
        i_avg, i_pp = sum(i_cc) / len(i_cc), max(i_cc) - min(i_cc)
        i_pk = max(window(t, cur, 0.6e-3, 1.0e-3))
        v_ov = max(window(t, vs, 1.6e-3, 2.4e-3))
        v_end_w = window(t, vs, 2.2e-3, 2.4e-3)
        v_end = sum(v_end_w) / len(v_end_w)
        checks = {
            f"前 {v_pre:.3f}V": abs(v_pre - VSET) <= 0.02 * VSET,
            f"CC 平均 {i_avg:.3f}A": abs(i_avg - ISET) <= 0.1 * ISET,
            f"CC 揺れ {i_pp:.3f}A": i_pp <= 0.6,
            f"突入 {i_pk:.2f}A": i_pk <= 2.0,
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
