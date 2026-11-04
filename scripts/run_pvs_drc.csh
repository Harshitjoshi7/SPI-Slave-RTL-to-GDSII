#!/bin/csh -f
###############################################################################
# Cadence PVS DRC Signoff Run Script for spi_slave (45nm GPDK)
###############################################################################

mkdir -p pvs_output/drc

pvs -drc \
  -gds output/spi_slave.gds \
  -top_cell spi_slave \
  -run_dir pvs_output/drc \
  /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlDRC.rul

echo ""
echo "=============================================="
echo "=== PVS DRC EXECUTION FINISHED ==="
echo "Report file: pvs_output/drc/spi_slave.sum"
echo "=============================================="
