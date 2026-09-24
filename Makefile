SHELL := /bin/bash
EDA_IMAGE := docker.io/hpretl/iic-osic-tools:2026.08
ROOT := $(CURDIR)

.PHONY: check python-test rtl-test experiment yosys-stat container-check clean

check: python-test rtl-test experiment yosys-stat

python-test:
	python3 -m unittest discover -s tests -p 'test_ble_model.py' -v

rtl-test:
	$(MAKE) -C tests -f Makefile.cocotb

experiment:
	PYTHONPATH=$(ROOT) EDA_IMAGE=$(EDA_IMAGE) python3 scripts/run_experiment.py

yosys-stat:
	@mkdir -p reports
	yosys -p 'read_verilog -sv rtl/ble_crc24.sv rtl/ble_whitener.sv rtl/ble_phy_loop.sv; hierarchy -check -top ble_phy_loop; proc; opt; stat' | tee reports/yosys-stat.txt

container-check:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		--entrypoint /bin/bash \
		-e HOME=/tmp \
		-e EDA_IMAGE=$(EDA_IMAGE) \
		-v '$(ROOT):/foss/designs/cgm-radio-lab' \
		-w /foss/designs/cgm-radio-lab \
		$(EDA_IMAGE) \
		-lc 'make check'

clean:
	$(MAKE) -C tests -f Makefile.cocotb clean
	$(RM) reports/experiment.json reports/per_curve.csv reports/yosys-stat.txt
