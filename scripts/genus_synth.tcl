###############################################################################
# Cadence Genus Synthesis Script for spi_slave
# Usage: genus -f scripts/genus_synth.tcl
###############################################################################

#==============================================================================
# 0. Create Output Directories
#    Without this, report/write commands WILL fail with "file not found"
#==============================================================================
file mkdir reports
file mkdir netlist

#==============================================================================
# 1. Setup Paths & Libraries (45nm GPDK / Digital Kit)
#==============================================================================

# Library search paths
set_db / .init_lib_search_path {
    /home/ec/install/FOUNDRY/digital/45nm/dig/lib
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing
}
set_db / .init_hdl_search_path {./src}

# Target technology library (.lib)
set_db / .library {/home/ec/install/FOUNDRY/digital/45nm/dig/lib/typical.lib}

# Physical LEF (for area and wireload estimation)
if {[file exists /home/ec/install/FOUNDRY/digital/45nm/dig/lef/tech.lef]} {
    set_db / .lef_library {
        /home/ec/install/FOUNDRY/digital/45nm/dig/lef/tech.lef
        /home/ec/install/FOUNDRY/digital/45nm/dig/lef/cells.lef
    }
} elseif {[file exists /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef]} {
    set_db / .lef_library {
        /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef
        /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/lef/gsclib045_macro.lef
    }
}

#==============================================================================
# 2. Read HDL & Elaborate
#==============================================================================
read_hdl -verilog src/spi_slave.v
elaborate spi_slave

# Check for any elaboration errors or unresolved references
check_design -unresolved

#==============================================================================
# 3. Read Timing Constraints
#==============================================================================
read_sdc constraints/spi_slave.sdc

# Verify constraints were loaded correctly
report_clocks > reports/clocks_synth.rpt

#==============================================================================
# 4. Synthesis Execution (3-step)
#==============================================================================

# Step 1: Generic Synthesis (RTL → GTECH technology-independent logic)
syn_generic
report_timing > reports/timing_generic.rpt

# Step 2: Technology Mapping (GTECH → target standard cell library)
syn_map
report_timing > reports/timing_mapped.rpt

# Step 3: Logic Optimization (area, power, timing optimization)
syn_opt

#==============================================================================
# 5. Post-Synthesis Checks
#==============================================================================

# Check for design rule violations
check_design -all > reports/check_design_synth.rpt

# Check for timing violations (negative slack = fail)
check_timing_intent > reports/check_timing_intent.rpt

#==============================================================================
# 6. Reports
#==============================================================================
report_timing -nworst 10 > reports/timing_synth.rpt
report_timing            > reports/timing_setup_synth.rpt
report_area              > reports/area_synth.rpt
report_power             > reports/power_synth.rpt
report_gates             > reports/gates_synth.rpt
report_qor               > reports/qor_synth.rpt
report_dp                > reports/datapath_synth.rpt
report_messages           > reports/messages_synth.rpt

#==============================================================================
# 7. Export Deliverables
#==============================================================================

# Gate-level netlist (Verilog)
write_hdl > netlist/spi_slave_synth.v

# SDC for PnR (forward-annotated constraints including clock groups)
write_sdc > netlist/spi_slave_synth.sdc

# SDF delay file (for gate-level simulation)
write_sdf > netlist/spi_slave_synth.sdf

# Design database (for re-loading into Genus later)
write_design -innovus -base_name netlist/spi_slave_genus

puts "=== Genus Synthesis Complete ==="
puts "=== Check reports/ directory for timing, area, power results ==="
