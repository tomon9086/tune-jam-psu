# 検証パイプラインの使い方（P1.5）

要件定義書 6.5 節（VER-01〜10）を実行する仕組み。回路は `hw/tune_jam_psu/` に circuit-synth（Python）で書き、`make verify` で回路図の生成からチェックまでをまとめて回す。

## 1. 準備

### KiCad 9（kicad-cli）

Ubuntu 24.04 標準の KiCad 7 には `kicad-cli sch erc` がないので、公式 PPA から KiCad 9 を入れる。

```sh
# クラウド環境では add-apt-repository が動かない（python3 が 3.13 のため）ので、手で登録する
curl -s "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0xFDA854F61C4D0D9572BB95E5245D5502FAD7A805" \
  | gpg --dearmor > /etc/apt/trusted.gpg.d/kicad-9.gpg
echo "deb https://ppa.launchpadcontent.net/kicad/kicad-9.0-releases/ubuntu noble main" \
  > /etc/apt/sources.list.d/kicad-9.list
apt-get update && apt-get install -y --no-install-recommends kicad kicad-symbols kicad-footprints
mkdir -p ~/.config/kicad/9.0
cp /usr/share/kicad/template/sym-lib-table /usr/share/kicad/template/fp-lib-table ~/.config/kicad/9.0/
```

ネットワーク設定で `ppa.launchpadcontent.net`、`api.launchpad.net`、`keyserver.ubuntu.com` を許可しておく。

### ngspice と Python の環境

```sh
apt-get install -y ngspice
make setup        # .venv を作り、hw/requirements.txt（circuit-synth==0.12.1）を入れる
```

## 2. 実行

```sh
make verify          # まとめて実行。結果は画面と build/verify_report.md
make verify-strict   # 発注前：LCSC 番号が未決定の部品をエラーにする
make sch             # 回路図の生成だけ（build/hw/tune_jam_psu/ を KiCad で開ける）
```

## 3. 各チェックの中身

| 項目 | スクリプト | 何を見るか |
|---|---|---|
| 回路図の生成 | `hw/build.py` | コードから KiCad の回路図を作る。毎回 `build/hw` を消して作り直す。意図した接続（`expected_nets.json`）と部品の一覧（`components.json`）も出す |
| VER-01 ERC | `tools/verify/erc_check.py` | `kicad-cli sch erc` のエラーのうち、許可リスト（`hw/erc_waivers.json`）にないものを数える |
| VER-03f 往復チェック | `tools/verify/netlist_diff.py` | コードで意図した接続と、KiCad の回路図から出したネットリストを双方向に突き合わせる |
| VER-05 BOM | `tools/verify/bom_check.py` | LCSC 番号の有無、JLC での区分と在庫、Extended の種類数（上限 8）。手はんだの部品は購入先の有無 |
| VER-07 出力スイッチ | `sim/output-switch/check.py` | ngspice で 6 条件と逆流を回し、Vgs、OFF までの時間、逆流電流の合否を出す |

まだないもの：VER-02 DRC（P3 で PCB ができてから）、VER-03 の (a)〜(e)、VER-04 ピン照合、VER-06 設計計算、VER-07 の降圧 IC（モデルの手直し中）、VER-08 FW のテスト。

## 4. わざと壊して試した結果（2026-11-09）

出力コンデンサ（C6、C8）の GND 側の接続をコードから消して `make verify` を回した。

- 最初は往復チェックが不一致を出した。調べると、**circuit-synth は既存のプロジェクトがあると「更新」し、古い接続（消したはずの GND）が回路図に残っていた**。`hw/build.py` で毎回作り直すように直した
- 直した後は、往復チェックは一致し、**ERC が「C6・C8 の 2 番ピンが未接続」をエラーとして出した**
- 元に戻すと全項目が合格に戻ることを確認した

## 5. 回路を書くときの決まり

- 部品は `hw/tune_jam_psu/parts.py` のヘルパーを使い、JLC で実装する部品には `LCSC="C…"` を付ける。値を決めていない受動部品は `"TODO"` のままでよい（`make verify-strict` でエラーになる）
- 手はんだの部品は `hand(...)` で作り、`Supplier`（購入先と型番）を書く
- 1 つの機能を 1 つのサブ回路（`@circuit`）にする。回路図ではシートが分かれ、読みやすくなる
- 使わないピンや、外から電源が来るネットの ERC エラーは、`hw/erc_waivers.json` に理由を書いて許可する

## 6. circuit-synth 0.12.1 の既知の制約

- 未接続の印（no_connect）と PWR_FLAG を回路図に書き出せない → 許可リストで扱う。数が増えてきたら、後処理で印を書き足すことを検討する
- 1 枚の図でも階層ラベルを使う → `hw/build.py` で global_label に置き換えている
- 既存のプロジェクトを「更新」する → 毎回作り直している
- 回路図の部品の配置はばらばら → レビューはコードの差分と検証結果を主にする
