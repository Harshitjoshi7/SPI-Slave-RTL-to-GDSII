###############################################################################
# Cadence PVS Signoff Script from inside Innovus
# Uses official 45nm GPDK PVS rules:
#   DRC: /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlDRC.rul
#   LVS: /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlLVS.rul
###############################################################################

file mkdir pvs_output/drc
file mkdir pvs_output/lvs

#==============================================================================
# PVS Signoff DRC
#==============================================================================
puts "\n--- Running PVS Signoff DRC ---"
set_verify_drc_mode -disable_rules {}
set_signoff_mode -engine pvs
set_signoff_drc_mode \
    -exec_script_in_innovus   1 \
    -rule_file                /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlDRC.rul \
    -rundir                   pvs_output/drc

catch {signoff_drc}
puts "\n[INFO] PVS DRC run initiated. Check pvs_output/drc/ for results."

#==============================================================================
# PVS Signoff LVS
#==============================================================================
puts "\n--- Running PVS Signoff LVS ---"
set_signoff_lvs_mode \
    -exec_script_in_innovus   1 \
    -rule_file                /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlLVS.rul \
    -reference_netlist_files  netlist/spi_slave_postroute_pg.v \
    -rundir                   pvs_output/lvs

catch {signoff_lvs}
puts "\n[INFO] PVS LVS run initiated. Check pvs_output/lvs/ for results."
