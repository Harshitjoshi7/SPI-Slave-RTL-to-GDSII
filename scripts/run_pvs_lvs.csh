#!/bin/csh -f
###############################################################################
# Cadence PVS LVS Signoff Run Script for spi_slave (45nm GPDK)
###############################################################################

mkdir -p pvs_output/lvs

pvs -lvs \
  -automatch \
  -hcell scripts/hcells.txt \
  -gds output/spi_slave.gds \
  -top_cell spi_slave \
  -source_top_cell spi_slave \
  -source_verilog netlist/spi_slave_lvs.v \
  -source_cdl /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/cdl/gsclib045.cdl \
  -control scripts/pvs_lvs.ctrl \
  -run_dir pvs_output/lvs \
  /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlLVS.rul

echo ""
echo "=============================================="
echo "=== PVS LVS EXECUTION FINISHED ==="
echo "Report file: pvs_output/lvs/spi_slave.rep"
echo "=============================================="
