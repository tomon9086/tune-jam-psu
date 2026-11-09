# 検証パイプライン（要件定義書 6.5 節）
# 前提：KiCad 9（kicad-cli）と ngspice が入っていること（docs/verification.md）

VENV ?= .venv
PY := $(VENV)/bin/python

.PHONY: setup sch verify verify-strict clean

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

clean:
	rm -rf build sim/output-switch/case_*.cir
