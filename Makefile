# 検証パイプライン（要件定義書 6.5 節）
# 前提：KiCad 9（kicad-cli）と ngspice が入っていること（docs/verification.md）

VENV ?= .venv
PY := $(VENV)/bin/python

.PHONY: setup sch verify verify-strict sim-slow clean

setup:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r hw/requirements.txt
	@command -v kicad-cli >/dev/null || echo "注意：kicad-cli がない（KiCad 9 を入れる）"
	@command -v ngspice >/dev/null || echo "注意：ngspice がない（apt-get install -y ngspice）"

sch:
	$(PY) hw/build.py

verify:
	$(PY) tools/verify/run_all.py

verify-strict:
	$(PY) tools/verify/run_all.py --strict

# 時間のかかるシミュレーション（LMR33630 のモデルを使う。1 本 10〜15 分）
sim-slow:
	cd sim/lmr33630 && ./get_model.sh
	cd sim/cc-loop && python3 gen.py && for n in d_mid_h4n7; do ngspice -b $$n.cir > $$n.log 2>&1; done && python3 check.py d_mid_h4n7

clean:
	rm -rf build sim/output-switch/case_*.cir
