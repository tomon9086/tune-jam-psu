#!/bin/sh
# TI の LMR33630A の PSpice モデル（暗号化されていないもの）を取得し、ngspice 用に書き換える。
# モデルは TI の著作物なのでリポジトリには入れない（models/ は .gitignore）。
set -e
cd "$(dirname "$0")"
mkdir -p models
curl -sSL -o models/snvmbf9a.zip https://www.ti.com/lit/zip/snvmbf9a
(cd models && unzip -oq snvmbf9a.zip)
python3 ../../tools/spice/pspice2ngspice.py models/LMR33630A_PSPICE_TRANS/LMR33630A_TRANS.lib models/lmr33630a_ng.lib
echo 'set ngbehavior=psa' > .spiceinit
echo "OK: models/lmr33630a_ng.lib"
