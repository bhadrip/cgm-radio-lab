SHELL := /bin/bash
EDA_IMAGE := docker.io/hpretl/iic-osic-tools:2026.08
ROOT := $(CURDIR)
GF180_TEMPLATE := third_party/gf180mcu-project-template
GF180_PDK_ROOT ?= /foss/pdks
GF180_CONFIGS := wafer_space/librelane-cgm.yaml

.PHONY: check python-test rtl-test experiment yosys-stat wafer-space-yosys container-check gf180-floorplan container-gf180-floorplan gf180-route container-gf180-route gf180-signoff container-gf180-signoff clean

check: python-test rtl-test experiment yosys-stat wafer-space-yosys

python-test:
	python3 -m unittest discover -s tests -p 'test_ble_model.py' -v

rtl-test:
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=ble_phy_loop COCOTB_TEST_MODULES=test_ble_phy_loop SIM_BUILD=sim_build/phy
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_packet_loop COCOTB_TEST_MODULES=test_cgm_packet_loop SIM_BUILD=sim_build/packet
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_chip_core COCOTB_TEST_MODULES=test_cgm_chip_core SIM_BUILD=sim_build/chip_core
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=chip_core COCOTB_TEST_MODULES=test_wafer_space_chip_core SIM_BUILD=sim_build/wafer_space

experiment:
	PYTHONPATH=$(ROOT) EDA_IMAGE=$(EDA_IMAGE) python3 scripts/run_experiment.py

yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv rtl/*.sv; hierarchy -check -top cgm_chip_core; proc; opt; tee -o reports/yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/yosys-stat.txt

wafer-space-yosys:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv rtl/*.sv wafer_space/chip_core.sv; hierarchy -check -top chip_core; proc; opt; tee -o reports/wafer-space-yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/wafer-space-yosys-stat.txt

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

gf180-floorplan:
	$(MAKE) -C $(GF180_TEMPLATE) SLOT=0p5x0p5 defines
	librelane $(GF180_CONFIGS) \
		--manual-pdk --pdk-root $(GF180_PDK_ROOT) --pdk gf180mcuD \
		--scl gf180mcu_fd_sc_mcu7t5v0 --pad gf180mcu_fd_io \
		--run-tag cgm-floorplan --overwrite --to OpenROAD.Floorplan \
		--condensed --hide-progress-bar

container-gf180-floorplan:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		--entrypoint /bin/bash \
		-e HOME=/tmp \
		-v '$(ROOT):/foss/designs/cgm-radio-lab' \
		-w /foss/designs/cgm-radio-lab \
		$(EDA_IMAGE) \
		-lc 'make gf180-floorplan'

gf180-route:
	$(MAKE) -C $(GF180_TEMPLATE) SLOT=0p5x0p5 defines
	librelane $(GF180_CONFIGS) \
		--manual-pdk --pdk-root $(GF180_PDK_ROOT) --pdk gf180mcuD \
		--scl gf180mcu_fd_sc_mcu7t5v0 --pad gf180mcu_fd_io \
		--run-tag cgm-route --overwrite --to OpenROAD.DetailedRouting \
		--condensed --hide-progress-bar

container-gf180-route:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		--entrypoint /bin/bash \
		-e HOME=/tmp \
		-v '$(ROOT):/foss/designs/cgm-radio-lab' \
		-w /foss/designs/cgm-radio-lab \
		$(EDA_IMAGE) \
		-lc 'make gf180-route'

gf180-signoff:
	$(MAKE) -C $(GF180_TEMPLATE) SLOT=0p5x0p5 defines
	librelane $(GF180_CONFIGS) \
		--manual-pdk --pdk-root $(GF180_PDK_ROOT) --pdk gf180mcuD \
		--scl gf180mcu_fd_sc_mcu7t5v0 --pad gf180mcu_fd_io \
		--run-tag cgm-signoff --overwrite \
		--condensed --hide-progress-bar

container-gf180-signoff:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		--entrypoint /bin/bash \
		-e HOME=/tmp \
		-v '$(ROOT):/foss/designs/cgm-radio-lab' \
		-w /foss/designs/cgm-radio-lab \
		$(EDA_IMAGE) \
		-lc 'make gf180-signoff'

clean:
	$(MAKE) -C tests -f Makefile.cocotb clean
	$(RM) reports/experiment.json reports/per_curve.csv reports/yosys-stat.txt reports/wafer-space-yosys-stat.txt
