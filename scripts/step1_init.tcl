###############################################################################
# STEP 1: Design Initialization
# Usage inside Innovus:  source scripts/step1_init.tcl
###############################################################################

# Create output directories
file mkdir reports
file mkdir netlist
file mkdir output

#--- Configure design import via global variables ---
set init_mmmc_file scripts/mmmc.tcl
set init_lef_file {/home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/lef/gsclib045_macro.lef}
set init_verilog netlist/spi_slave_synth.v
set init_top_cell spi_slave

#--- Initialize Design (loads MMMC + LEF + netlist all at once) ---
init_design

puts "\n=== STEP 1 COMPLETE: Design initialized successfully ==="
puts "=== Next: source scripts/step2_floorplan.tcl ==="
