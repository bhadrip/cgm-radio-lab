SHELL := /bin/bash
EDA_IMAGE := docker.io/hpretl/iic-osic-tools:2026.08
ROOT := $(CURDIR)
GF180_TEMPLATE := third_party/gf180mcu-project-template
GF180_PDK_ROOT ?= /foss/pdks
GF180_CONFIGS := wafer_space/librelane-cgm.yaml
CORE_RTL := $(filter-out rtl/ble_dco_dac_decoder.sv,$(wildcard rtl/*.sv))

.PHONY: check python-test rtl-test analog-test ring-dco-test lc-vco-test lc-dco-test gf180-fast-dac-test gf180-fast-dac-steered-test gf180-fast-dac-steered-pvt-test gf180-fast-dac-mismatch-test gf180-fast-dac-gate-driver-test gf180-fast-dac-reference-window-test gf180-pa-test gf180-pa-load-test gf180-pa-match-test gf180-lna-test gf180-lna-band-test gf180-lna-linearity-test gf180-lna-bias-boost-test pa-match-screen gfsk-spectrum rx-noise-budget lc-dco-local-calibration lc-dco-dynamic-test lc-dco-drive-settling rf-characterization container-rf-characterization dco-bank-sizing dco-modulation dco-dac-resolution dco-segmented-dac dco-dac-nonidealities dco-dac-transition experiment yosys-stat gfsk-yosys-stat gfsk-tx-yosys-stat dco-yosys-stat dco-dac-yosys-stat wafer-space-yosys container-check gf180-floorplan container-gf180-floorplan gf180-route container-gf180-route gf180-signoff container-gf180-signoff clean

check: python-test rtl-test analog-test dco-bank-sizing dco-modulation gfsk-spectrum pa-match-screen rx-noise-budget dco-dac-resolution dco-segmented-dac dco-dac-nonidealities dco-dac-transition experiment yosys-stat gfsk-yosys-stat gfsk-tx-yosys-stat dco-yosys-stat dco-dac-yosys-stat wafer-space-yosys

python-test:
	python3 -m unittest discover -s tests -p 'test_*model.py' -v

rtl-test:
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=ble_gfsk_modulator COCOTB_TEST_MODULES=test_ble_gfsk_modulator SIM_BUILD=sim_build/gfsk
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=ble_dco_controller COCOTB_TEST_MODULES=test_ble_dco_controller SIM_BUILD=sim_build/dco
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=ble_dco_dac_decoder COCOTB_TEST_MODULES=test_ble_dco_dac_decoder SIM_BUILD=sim_build/dco_dac_decoder
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_gfsk_tx COCOTB_TEST_MODULES=test_cgm_gfsk_tx SIM_BUILD=sim_build/gfsk_tx
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=ble_phy_loop COCOTB_TEST_MODULES=test_ble_phy_loop SIM_BUILD=sim_build/phy
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_packet_loop COCOTB_TEST_MODULES=test_cgm_packet_loop SIM_BUILD=sim_build/packet
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=cgm_chip_core COCOTB_TEST_MODULES=test_cgm_chip_core SIM_BUILD=sim_build/chip_core
	$(MAKE) -C tests -f Makefile.cocotb TOPLEVEL=chip_core COCOTB_TEST_MODULES=test_wafer_space_chip_core SIM_BUILD=sim_build/wafer_space

analog-test: ring-dco-test lc-vco-test lc-dco-test gf180-fast-dac-test gf180-fast-dac-reference-window-test gf180-pa-load-test gf180-pa-match-test gf180-lna-band-test gf180-lna-linearity-test gf180-lna-bias-boost-test

ring-dco-test:
	python3 scripts/run_ring_dco_sweep.py

lc-vco-test:
	python3 scripts/run_lc_vco_sweep.py

lc-dco-test:
	python3 scripts/run_lc_dco_sweep.py

gf180-fast-dac-test: dco-dac-transition
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_fast_dac.py

gf180-fast-dac-steered-test: dco-dac-transition
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_fast_dac_steered.py

gf180-fast-dac-steered-pvt-test: gf180-fast-dac-steered-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_fast_dac_steered_pvt.py

gf180-fast-dac-mismatch-test: gf180-fast-dac-steered-pvt-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_fast_dac_mismatch.py

gf180-fast-dac-gate-driver-test: dco-dac-transition
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_fast_dac_gate_driver.py

gf180-fast-dac-reference-window-test: gf180-fast-dac-mismatch-test gf180-fast-dac-gate-driver-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_fast_dac_reference_window.py

gf180-pa-test:
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_pa.py

gf180-pa-load-test: gf180-pa-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_pa_load_sweep.py

gf180-pa-match-test: gf180-pa-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_pa_match.py

gf180-lna-test:
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_lna.py

gf180-lna-band-test: gf180-lna-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_lna_band.py

gf180-lna-linearity-test: gf180-lna-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_lna_linearity.py

gf180-lna-bias-boost-test: gf180-lna-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_lna_bias_boost.py

pa-match-screen:
	PYTHONPATH=$(ROOT) python3 scripts/size_pa_match.py

rx-noise-budget:
	PYTHONPATH=$(ROOT) python3 scripts/run_rx_noise_budget.py

gfsk-spectrum:
	PYTHONPATH=$(ROOT) python3 scripts/run_gfsk_spectrum.py

lc-dco-local-calibration:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_local_calibration.py

lc-dco-dynamic-test:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_dynamic.py

rf-characterization:
	$(MAKE) lc-dco-test
	$(MAKE) lc-dco-local-calibration
	$(MAKE) dco-modulation
	$(MAKE) dco-dac-resolution
	$(MAKE) dco-segmented-dac
	$(MAKE) dco-dac-nonidealities
	$(MAKE) gf180-fast-dac-test
	$(MAKE) gf180-fast-dac-reference-window-test
	$(MAKE) gf180-pa-load-test
	PYTHONPATH=$(ROOT) python3 scripts/run_gf180_pa_match.py
	$(MAKE) gf180-lna-band-test
	$(MAKE) gf180-lna-linearity-test
	$(MAKE) gf180-lna-bias-boost-test
	$(MAKE) pa-match-screen
	$(MAKE) rx-noise-budget
	$(MAKE) gfsk-spectrum
	$(MAKE) lc-dco-drive-settling
	$(MAKE) lc-dco-dynamic-test

container-rf-characterization:
	docker run --rm \
		--user $$(id -u):$$(id -g) \
		--entrypoint /bin/bash \
		-e HOME=/tmp \
		-e LC_DCO_JOBS=2 \
		-v '$(ROOT):/foss/designs/cgm-radio-lab' \
		-w /foss/designs/cgm-radio-lab \
		$(EDA_IMAGE) \
		-lc 'make rf-characterization'

dco-bank-sizing:
	PYTHONPATH=$(ROOT) python3 scripts/size_lc_dco_bank.py

dco-modulation:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_modulation.py

dco-dac-resolution:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_dac_resolution.py

dco-segmented-dac:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_segmented_dac.py

dco-dac-nonidealities:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_dac_nonidealities.py

dco-dac-transition:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_dac_transition.py

lc-dco-drive-settling:
	PYTHONPATH=$(ROOT) python3 scripts/run_lc_dco_drive_settling.py

experiment:
	PYTHONPATH=$(ROOT) EDA_IMAGE=$(EDA_IMAGE) python3 scripts/run_experiment.py

yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv $(CORE_RTL); hierarchy -check -top cgm_chip_core; proc; opt; tee -o reports/yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/yosys-stat.txt

gfsk-yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv rtl/ble_gfsk_modulator.sv; hierarchy -check -top ble_gfsk_modulator; proc; opt; tee -o reports/gfsk-yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/gfsk-yosys-stat.txt

gfsk-tx-yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv $(CORE_RTL); hierarchy -check -top cgm_gfsk_tx; proc; opt; tee -o reports/gfsk-tx-yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/gfsk-tx-yosys-stat.txt

dco-yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv rtl/ble_dco_controller.sv; hierarchy -check -top ble_dco_controller; proc; opt; tee -o reports/dco-yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/dco-yosys-stat.txt

dco-dac-yosys-stat:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv rtl/ble_dco_dac_decoder.sv; hierarchy -check -top ble_dco_dac_decoder; proc; opt; tee -o reports/dco-dac-yosys-stat.txt stat'
	perl -0pi -e 's/[ \t]+$$//mg; s/\n+\z/\n/' reports/dco-dac-yosys-stat.txt

wafer-space-yosys:
	@mkdir -p reports
	yosys -q -p 'read_verilog -sv $(CORE_RTL) wafer_space/chip_core.sv; hierarchy -check -top chip_core; proc; opt; tee -o reports/wafer-space-yosys-stat.txt stat'
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
	$(RM) reports/experiment.json reports/per_curve.csv reports/ring_dco_sweep.json reports/ring_dco_sweep.csv reports/lc_vco_sweep.json reports/lc_vco_sweep.csv reports/lc_dco_bank.json reports/lc_dco_local_calibration.json reports/lc_dco_local_calibration.csv reports/lc_dco_modulation.json reports/lc_dco_modulation_nominal_ch37.csv reports/lc_dco_dac_resolution.json reports/lc_dco_segmented_dac.json reports/lc_dco_dac_nonidealities.json reports/lc_dco_dac_transition.json reports/gf180_fast_dac.json reports/gf180_fast_dac_steered.json reports/gf180_fast_dac_steered_pvt.json reports/gf180_fast_dac_mismatch.json reports/gf180_fast_dac_gate_driver.json reports/gf180_fast_dac_reference_window.json reports/gf180_pa.json reports/gf180_pa_load_sweep.json reports/gf180_pa_match.json reports/gf180_lna.json reports/gf180_lna_band.json reports/gf180_lna_linearity.json reports/gf180_lna_bias_boost.json reports/gfsk_spectrum.json reports/pa_match_screen.json reports/rx_noise_budget.json reports/lc_dco_drive_settling.json reports/lc_dco_dynamic.json reports/yosys-stat.txt reports/gfsk-yosys-stat.txt reports/gfsk-tx-yosys-stat.txt reports/dco-yosys-stat.txt reports/dco-dac-yosys-stat.txt reports/wafer-space-yosys-stat.txt
