###############################################################################
# Cadence Innovus MMMC Configuration for spi_slave (45nm GPDK)
# Uses GPDK045-specific timing libraries that match the LEF cell names
###############################################################################

# Slow corner (worst-case setup) — includes both basic cells and multibit DFFs
create_library_set -name slow_libs -timing {/home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/slow_vdd1v0_basicCells.lib /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/slow_vdd1v0_multibitsDFF.lib}

# Fast corner (best-case hold)
create_library_set -name fast_libs -timing {/home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/fast_vdd1v0_basicCells.lib /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/fast_vdd1v0_multibitsDFF.lib}

# RC corners
create_rc_corner -name slow_rc -temperature 125
create_rc_corner -name fast_rc -temperature 0

# Delay corners
create_delay_corner -name slow_delay -library_set slow_libs -rc_corner slow_rc
create_delay_corner -name fast_delay -library_set fast_libs -rc_corner fast_rc

# Constraint mode (SDC from Genus synthesis)
create_constraint_mode -name func_mode -sdc_files {netlist/spi_slave_synth.sdc}

# Analysis views
create_analysis_view -name slow_view -constraint_mode func_mode -delay_corner slow_delay
create_analysis_view -name fast_view -constraint_mode func_mode -delay_corner fast_delay

# Setup = slow corner, Hold = fast corner
set_analysis_view -setup {slow_view} -hold {fast_view}
