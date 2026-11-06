#!/usr/bin/env python3
"""TI の PSpice モデル（暗号化されていないもの）を ngspice で読めるように書き換える。

使い方:
    python3 tools/spice/pspice2ngspice.py 入力.lib 出力.lib

行う書き換え（LMR33630A_TRANS.lib で必要だったもの）:
  1. .PARAM の中で、後ろで定義される値を先に参照している → 依存関係の順に並べ替え、1 行 1 個にする
  2. {{a-b}/{c-d}} のような入れ子の波括弧 → 内側を丸括弧にする
  3. 行の折り返しで "< 0 .5" のように数値が切れている → "< 0.5" に直す

ngspice 側では .spiceinit に `set ngbehavior=psa` を入れて PSpice 互換モードにすること。
モデル本体（TI の著作物）はリポジトリに入れず、TI のサイトから取得する。
"""
import re
import sys

PARAM_ITEM = re.compile(r"(\w+)\s*=\s*(\{(?:[^{}]|\{[^{}]*\})*\}|[^\s]+)")


def reorder_params(body: str) -> list[str]:
    items = [(m.group(1).lower(), m.group(2)) for m in PARAM_ITEM.finditer(body)]
    names = {n for n, _ in items}
    done: set[str] = set()
    ordered = []
    pending = items[:]
    while pending:
        progressed = False
        for item in pending[:]:
            deps = set(re.findall(r"[a-z_]\w*", item[1].lower())) & names
            if deps <= done:
                ordered.append(item)
                done.add(item[0])
                pending.remove(item)
                progressed = True
        if not progressed:
            raise SystemExit(f"循環参照があります: {pending}")
    out = []
    for name, value in ordered:
        if value.startswith("{") and value.endswith("}"):
            inner = value[1:-1].replace("{", "(").replace("}", ")")
            value = "{" + inner + "}"
        out.append(f".param {name}={value}")
    return out


def convert(text: str) -> str:
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].upper().startswith(".PARAM"):
            body = lines[i][6:]
            j = i + 1
            while j < len(lines) and lines[j].startswith("+"):
                body += " " + lines[j][1:]
                j += 1
            out.extend(reorder_params(body))
            i = j
        else:
            out.append(lines[i])
            i += 1
    result = "\n".join(out)
    result = re.sub(r"<\s*0 \.(\d)", r"< 0.\1", result)
    return result


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding="latin-1") as f:
        text = f.read()
    with open(dst, "w", encoding="utf-8") as f:
        f.write(convert(text))


if __name__ == "__main__":
    main()
