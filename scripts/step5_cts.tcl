###############################################################################
# STEP 5: Clock Tree Synthesis (CTS) using CCOpt
# Usage inside Innovus:  source scripts/step5_cts.tcl
###############################################################################

# Set CTS buffer/inverter cells (try common GPDK045 cell names)
catch {set_ccopt_property buffer_cells {CLKBUFX2 CLKBUFX4 CLKBUFX8 BUFX2 BUFX4 BUFX8}}
catch {set_ccopt_property inverter_cells {CLKINVX1 CLKINVX2 CLKINVX4 INVX1 INVX2 INVX4}}

# CTS constraints
set_ccopt_property target_max_trans 0.3
set_ccopt_property target_skew 0.1

# Generate CTS spec and source it
create_ccopt_clock_tree_spec -file ccopt.spec
source ccopt.spec

# Run CTS
ccopt_design -cts

# Post-CTS timing (setup)
timeDesign -postCTS -outDir reports

# Post-CTS optimization (setup + hold)
optDesign -postCTS
optDesign -postCTS -hold

# Post-CTS timing (hold)
timeDesign -postCTS -hold -outDir reports

puts "\n=== STEP 5 COMPLETE: Clock tree synthesized ==="
puts "=== Check reports/ for post-CTS timing ==="
puts "=== Next: source scripts/step6_route.tcl ==="
