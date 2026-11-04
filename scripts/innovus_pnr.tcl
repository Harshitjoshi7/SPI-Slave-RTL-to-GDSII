###############################################################################
# Cadence Innovus Place & Route Script for spi_slave
# Usage: innovus -stylus -f scripts/innovus_pnr.tcl
#        (or classic mode: innovus -init scripts/innovus_pnr.tcl)
###############################################################################

#==============================================================================
# 0. Create Output Directories
#==============================================================================
file mkdir reports
file mkdir reports/preCTS
file mkdir reports/postCTS
file mkdir reports/postCTS_hold
file mkdir reports/postRoute
file mkdir reports/postRoute_hold
file mkdir reports/signoff
file mkdir reports/signoff_hold
file mkdir netlist
file mkdir output
file mkdir pvs_output
file mkdir pvs_output/drc
file mkdir pvs_output/lvs

# Reset any previous session state
catch {freeDesign}

# --- Read MMMC Configuration ---
read_mmmc scripts/mmmc.tcl

# --- Read Physical Data (LEF) ---
read_physical -lefs {
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/lef/gsclib045_macro.lef
}

# --- Read Synthesized Gate Netlist ---
read_netlist netlist/spi_slave_synth.v -top spi_slave

# --- Initialize Design Database ---
init_design

#==============================================================================
# 2. Floorplanning
#==============================================================================

# Define floorplan: aspect ratio 1.0, core utilization 65%
floorPlan -r 1.0 0.65 10 10 10 10
# Arguments: -r <aspect_ratio> <utilization> <left> <bottom> <right> <top> margins

# Edit pin placement on Metal3
editPin -side North -pin {clock resetb} -layer Metal3
editPin -side East  -pin {MISO}         -layer Metal3
editPin -side West  -pin {SCK CSB MOSI} -layer Metal3

#==============================================================================
# 3. Power Planning (PDN)
#==============================================================================

# Global net connections
globalNetConnect VDD -type pgpin -pin VDD -inst * -all
globalNetConnect VSS -type pgpin -pin VSS -inst * -all

# Power rings around core
addRing -type core_rings \
    -nets {VDD VSS} \
    -layer {top Metal5 bottom Metal5 left Metal4 right Metal4} \
    -width 1.5 -spacing 0.5 -offset 2.0

# Power stripes (vertical on Metal5, horizontal on Metal4)
addStripe -nets {VDD VSS} \
    -layer Metal5 -direction vertical \
    -width 1.0 -spacing 0.5 -set_to_set_distance 40 \
    -start_from left -start_offset 10

addStripe -nets {VDD VSS} \
    -layer Metal4 -direction horizontal \
    -width 1.0 -spacing 0.5 -set_to_set_distance 40 \
    -start_from bottom -start_offset 10

# Special route: connect standard cell VDD/VSS rails
sroute -connect {blockPin padPin corePin} \
    -layerChangeRange {Metal1 Metal5} \
    -blockPinTarget nearestTarget \
    -padPinPortConnect allPort \
    -allowJogging 1 \
    -allowLayerChange 1 \
    -nets {VDD VSS}

#==============================================================================
# 4. Placement
#==============================================================================

# Insert end caps and well taps (gracefully handles PDK cell variations)
catch {addEndCap -prefix ENDCAP}
catch {addWellTap -cell FILL1 -cellInterval 30 -prefix WELLTAP}
catch {addWellTap -cell WELLTAP -cellInterval 30 -prefix WELLTAP}

# Run placement (timing-driven with optimization)
place_opt_design

# Verify placement legality
checkPlace

# Pre-CTS timing report
timeDesign -preCTS -outDir reports/preCTS

#==============================================================================
# 5. Clock Tree Synthesis (CTS) using CCOpt
#==============================================================================

# CTS buffer/inverter cell candidates (supports GPDK045 and standard naming)
catch {set_ccopt_property buffer_cells {CLKBUFX2 CLKBUFX4 CLKBUFX8 BUFX2 BUFX4 BUFX8}}
catch {set_ccopt_property inverter_cells {CLKINVX1 CLKINVX2 CLKINVX4 INVX1 INVX2 INVX4}}

# CTS target skew & transition
set_ccopt_property target_max_trans 0.3
set_ccopt_property target_skew 0.1

# Generate and source CTS spec
create_ccopt_clock_tree_spec -file ccopt.spec
source ccopt.spec

# Run CTS
ccopt_design -cts

# Post-CTS timing: check setup, optimize, then check hold
timeDesign -postCTS -outDir reports/postCTS
optDesign  -postCTS
optDesign  -postCTS -hold
timeDesign -postCTS -hold -outDir reports/postCTS_hold

#==============================================================================
# 6. Filler Cell Insertion (BEFORE routing — required for DRC-clean layout)
#==============================================================================
catch {
    addFiller -cell {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1 FILLCELL64 FILLCELL32 FILLCELL16 FILLCELL8 FILLCELL4 FILLCELL2 FILLCELL1} -prefix FILLER
}

# Verify no placement gaps remain
checkPlace

#==============================================================================
# 7. Routing (NanoRoute)
#==============================================================================
routeDesign

# Post-route OCV analysis with CPPR
setAnalysisMode -analysisType onChipVariation -cppr both

# Post-route optimization (setup + hold)
optDesign -postRoute
optDesign -postRoute -hold

# Post-route timing reports
timeDesign -postRoute      -outDir reports/postRoute
timeDesign -postRoute -hold -outDir reports/postRoute_hold

#==============================================================================
# 8. Metal Fill Insertion (post-route, for density DRC rules)
#==============================================================================
# Foundries require minimum metal density per layer.
# NOTE: Requires metal fill rule file from PDK.
# addMetalFill -layer {Metal1 Metal2 Metal3 Metal4 Metal5} \
#     -minDensity 0.2 -maxDensity 0.8

# Trim metal fill near signal nets (prevent coupling issues)
# trimMetalFill -deleteViols

#==============================================================================
# 9. Physical Verification (Internal — Quick Check)
#==============================================================================
verify_drc
verifyConnectivity -type all -error 1000 -warning 50
verifyProcessAntenna

#==============================================================================
# 10. Export Post-Route Netlists
#==============================================================================
# Logical netlist (for LEC and gate-level simulation)
saveNetlist netlist/spi_slave_postroute.v

# Netlist with PG pins (for PVS LVS signoff — must include VDD/VSS connections)
saveNetlist -includePowerGround netlist/spi_slave_postroute_pg.v

#==============================================================================
# 11. PVS Signoff Verification (Cadence PVS — Integrated Flow)
#==============================================================================
# NOTE: For standalone PVS flow (recommended for final tapeout), see:
#   scripts/pvs_drc.ctrl  →  pvs -drc -control scripts/pvs_drc.ctrl
#   scripts/pvs_lvs.ctrl  →  pvs -lvs -control scripts/pvs_lvs.ctrl

# --- PVS Signoff DRC (runs if rule file exists) ---
if {[file exists /home/ec/install/FOUNDRY/digital/45nm/pvs/drc.rul]} {
    set_signoff_mode -engine pvs
    set_signoff_drc_mode \
        -exec_script_in_innovus   1 \
        -rule_file                /home/ec/install/FOUNDRY/digital/45nm/pvs/drc.rul \
        -rundir                   pvs_output/drc
    signoff_drc
    puts "\n[INFO] PVS DRC results: pvs_output/drc/"
} else {
    puts "\n[INFO] Skipping integrated PVS DRC (drc.rul not found, run verify_drc instead)"
}

# --- PVS Signoff LVS (runs if rule file exists) ---
if {[file exists /home/ec/install/FOUNDRY/digital/45nm/pvs/lvs.rul]} {
    set_signoff_lvs_mode \
        -exec_script_in_innovus   1 \
        -rule_file                /home/ec/install/FOUNDRY/digital/45nm/pvs/lvs.rul \
        -reference_netlist_files  netlist/spi_slave_postroute_pg.v \
        -rundir                   pvs_output/lvs
    signoff_lvs
    puts "[INFO] PVS LVS results: pvs_output/lvs/"
} else {
    puts "[INFO] Skipping integrated PVS LVS (lvs.rul not found, run verifyConnectivity instead)"
}

#==============================================================================
# 12. Parasitic Extraction & Timing Signoff
#==============================================================================
setExtractRCMode -engine postRoute -effortLevel signoff
extractRC
rcOut -spef netlist/spi_slave_postroute.spef

# SDF for post-route gate-level simulation
write_sdf -version 3.0 netlist/spi_slave_postroute.sdf

# Final timing signoff with extracted parasitics
timeDesign -signoff      -outDir reports/signoff
timeDesign -signoff -hold -outDir reports/signoff_hold

#==============================================================================
# 13. GDSII Export
#==============================================================================
if {[file exists /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/gds/gds2.map]} {
    streamOut output/spi_slave.gds \
        -mapFile /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/gds/gds2.map \
        -libName spi_slave \
        -structureName spi_slave \
        -units 1000 \
        -mode ALL
} else {
    streamOut output/spi_slave.gds \
        -libName spi_slave \
        -structureName spi_slave \
        -units 1000 \
        -mode ALL
}

# Save Innovus design database (for re-loading and ECO changes)
saveDesign output/spi_slave_final.enc

puts "=== Innovus PnR Complete ==="
puts "=== Run 'lec -xl -do scripts/conformal_lec.tcl' for post-route LEC ==="
