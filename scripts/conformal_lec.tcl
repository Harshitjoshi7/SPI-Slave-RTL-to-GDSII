###############################################################################
# Cadence Conformal LEC (Logic Equivalence Checking) Script
#
# PURPOSE: Formally prove that the gate-level netlist is functionally
#          identical to the RTL source — no simulation vectors needed.
#          This is a mathematical proof, not a test. It catches:
#            - Synthesis optimization errors
#            - Clock gating insertion bugs
#            - Constant propagation mistakes
#            - FSM re-encoding errors
#
# WHEN TO RUN:
#   ① After Phase 3 (Genus Synthesis):  RTL vs. Gate-Level Netlist
#   ② After Phase 7 (Innovus Routing):  Gate-Level Netlist vs. Post-Route Netlist
#
# USAGE:
#   lec -xl -nogui -do scripts/conformal_lec.tcl
#   (or with GUI: lec -xl -do scripts/conformal_lec.tcl)
#
# This is EXTREMELY easy to run and gives 100% functional coverage.
###############################################################################

#==============================================================================
# 1. Setup
#==============================================================================
set_log_file lec_results.log -replace

# Set flattening rules for synthesis name changes
set_flatten_model -seq_constant -all
set_flatten_model -nodeset_to_constraint

#==============================================================================
# 2. Read Golden (Reference) Design = RTL
#==============================================================================
read_library -liberty /home/ec/install/FOUNDRY/digital/45nm/dig/lib/typical.lib -both

read_design src/spi_slave.v -verilog -golden -lastmod -norangeconstraint
set_root_module spi_slave -golden

#==============================================================================
# 3. Read Revised Design = Gate-Level Netlist
#==============================================================================
read_design netlist/spi_slave_synth.v -verilog -revised -lastmod -norangeconstraint
set_root_module spi_slave -revised

#==============================================================================
# 4. Set Constraints (match SDC for accurate comparison)
#==============================================================================
add_pin_constraint 1 resetb -golden
add_pin_constraint 1 resetb -revised

#==============================================================================
# 5. Map Key Points
#==============================================================================
set_system_mode lec

# Automatic mapping
map_key_points
report_unmapped_points

#==============================================================================
# 6. Add Compare Points & Run Comparison
#==============================================================================
add_compare_points -all
compare

#==============================================================================
# 7. Report Results
#==============================================================================
report_compare_data -nonequivalent
report_compare_data -equivalent -summary
report_verification

# Diagnose failures (if any)
diagnose -nonequivalent

#==============================================================================
# 8. Summary
#==============================================================================
puts ""
puts "========================================="
puts " LEC RESULT SUMMARY"
puts "========================================="
report_compare_data -summary

exit -f
