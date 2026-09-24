SHELL := /bin/bash
EDA_IMAGE := docker.io/hpretl/iic-osic-tools:2026.08
ROOT := $(CURDIR)

.PHONY: check python-test rtl-test experiment yosys-stat container-check clean

check: python-test rtl-test experiment yosys-stat

python-test:
	python3 -m unittest discover -s tests -p 'test_ble_model.py' -v

rtl-test:
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=ble_phy_loop COCOTB_TEST_MODULES=test_ble_phy_loop SIM_BUILD=sim_build/phy
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_packet_loop COCOTB_TEST_MODULES=test_cgm_packet_loop SIM_BUILD=sim_build/packet
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_chip_core COCOTB_TEST_MODULES=test_cgm_chip_core SIM_BUILD=sim_build/chip_core

experiment:
	PYTHONPATH=$(ROOT) EDA_IMAGE=$(EDA_IMAGE) python3 scripts/run_experiment.py

yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv rtl/*.sv; hierarchy -check -top cgm_chip_core; proc; opt; tee -o reports/yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/yosys-stat.txt

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
