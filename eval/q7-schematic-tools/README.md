# 回路図ツールの評価（Q7、2026-11-08）

同じ小さな回路（DC 入力 → TVS → LMR33630 の 5V 降圧 → AMS1117 の 3.3V）を各ツールで書き、KiCad 9 の `kicad-cli` で ERC とネットリストの出力まで通るかを試した。

## 環境

- KiCad 9.0.9（公式 PPA `ppa:kicad/kicad-9.0-releases`。Ubuntu 24.04 標準の KiCad 7 は `kicad-cli sch erc` がない）
- シンボルとフットプリントは KiCad 標準ライブラリ（`kicad-symbols`、`kicad-footprints`）。`~/.config/kicad/9.0/` に `/usr/share/kicad/template/` の `sym-lib-table` と `fp-lib-table` をコピーしておく
- SKiDL 3.0.0、tscircuit 0.0.3121（@tscircuit/cli 0.1.2446）、circuit-synth 0.12.1

## 結果

| 評価項目 | SKiDL | tscircuit | circuit-synth | atopile | EasyEDA MCP |
|---|---|---|---|---|---|
| 言語 | Python | TypeScript（TSX） | Python | 独自言語 | GUI 操作 |
| KiCad の回路図（.kicad_sch）を出せる | ✗ 自動配線で失敗（`RoutingFailure`） | ○ | ○ | ✗（PCB だけを作る設計） | ✗（EasyEDA 形式） |
| KiCad 9 で読める | — | △ 電源記号が KiCad 10 の書き方（`(power global)`）で、置き換えが要る | ○ | — | — |
| 書いたとおりの接続になる | ○（ネットリスト） | **✗ C5 の GND への接続が抜け落ちた**（tscircuit 自身のネットリストでは正しいのに、KiCad 変換で消えた） | **○ 全接続が一致**（LMR33630 の放熱パッドも GND） | — | — |
| `kicad-cli sch erc` | — | 105 件（座標のずれ 75 件、上記の接続抜けを含む） | ラベルの種類を置き換えた後、**5 件で、すべて本当の設計上の指摘**（PWR_FLAG なし、PG の未接続、フットプリント未登録） | — | — |
| シンボル | KiCad 標準 | tscircuit 独自（ピン配置を自分で書く。読み違いのリスク） | **KiCad 標準**（ピン名がライブラリで決まる。VER-04 に有利） | — | — |
| 回路図の見た目 | — | 線でつながった図。交差が多い | 部品をラベルでつなぐ図。部品がばらばらに並ぶ | — | — |
| 成熟度 | 長く使われている | 0.0.x で変化が速い | 0.12 で若い | — | — |
| ヘッドレスで動く | ○ | ○ | ○ | ○ | ✗（EasyEDA Pro の GUI が要る） |

- circuit-synth の回路図は、1 枚の図でも「階層ラベル」を使うので、KiCad の ERC がエラーにする。`(hierarchical_label` を `(global_label` に置き換えると消える（接続は正しい）
- atopile と EasyEDA MCP は、「回路図を人がレビューする」「`kicad-cli` で ERC を回す」という条件（MFG-07〜09、VER-01）を満たせないので、試作前に外した

## 接続の突き合わせ（往復チェック）

`tools/verify/netlist_diff.py` で、意図した接続（`expected_nets.json`）と、KiCad の回路図から `kicad-cli sch export netlist` で出したネットリストを比べた。ネット名ではなく「どのピンどうしが同じネットか」を比べる。

| ネット | circuit-synth | tscircuit |
|---|---|---|
| VIN、+5V、+3V3、SW、BOOT、VCC、FB | OK | OK（VIN の D1 は下記） |
| GND | **OK（10 ピン）** | **NG：C5 の 2 番ピンが未接続** |

- 最初、circuit-synth の GND で「U1.9 が余分」と出たが、これは LMR33630 の放熱パッドで、期待値に書き忘れていた。GND で正しい
- tscircuit の D1 が VIN と GND で逆に出るのは、tscircuit のダイオードの 1 番ピンがアノードという番号の決め方の違いで、接続の誤りではない
- 回路図の見た目では、circuit-synth は線ではなく電源記号（GND の記号）でつないでいるので、つながっていないように見えることがある（`circuit_synth_c5.png`）。tscircuit は、C5 から出た線が実際にどこにもつながっていない（`tscircuit_c5.png`）
- 画像どうしの差分は、2 つのツールで部品の配置がまったく違うので使えない。比べるべきは接続（ネットリスト）

## 推奨

**circuit-synth を使い、次の 2 つを検証パイプラインに入れる**

1. 生成後の後処理：ラベルの種類の置き換え（バージョンを固定し、更新したら外せるか確認する）
2. **往復チェック**：コードが意図したネットリストと、KiCad の回路図から `kicad-cli sch export netlist` で出したネットリストを突き合わせる。tscircuit で起きたような「変換で接続が消える」バグを機械的に見つけるため（VER-03 に追加）

見た目の問題（部品がばらばら）は、回路をブロックごとのサブ回路（シート）に分けて緩和する。レビューはコードの差分＋ネットリストの一覧＋回路図の画像で行う。

## ファイル

- `skidl_aux.py`、`tscircuit_aux.circuit.tsx`、`circuit_synth_aux.py`：評価に使ったコード
- `circuit_synth_schematic.png`、`tscircuit_schematic.png`：KiCad で SVG に書き出した回路図
- `circuit_synth_c5.png`、`tscircuit_c5.png`：C5 の周りの拡大
- `expected_nets.json`：往復チェックの期待値
- 注意：`tscircuit_aux.circuit.tsx` の LMR33630 のピン配置は、評価のために手で書いたもので、データシートとは照合していない
