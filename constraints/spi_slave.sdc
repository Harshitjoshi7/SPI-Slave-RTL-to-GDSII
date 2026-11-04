###############################################################################
# SDC Constraints for spi_slave
# Target: Cadence Genus (Synthesis) and Innovus (PnR)
###############################################################################

#==============================================================================
# Clock Definitions
#==============================================================================

# System clock: 20 MHz → 50 ns period
create_clock -name clk_sys -period 50.0 [get_ports clock]

# SPI clock: 2 MHz → 500 ns period
# SCK is an external input clock; define it for input delay analysis.
# Since SCK goes through CDC synchronizers, we treat it as a virtual clock
# for I/O delay constraints.
create_clock -name clk_sck -period 500.0 [get_ports SCK]

# SCK and system clock are asynchronous — set_clock_groups
set_clock_groups -asynchronous \
    -group [get_clocks clk_sys] \
    -group [get_clocks clk_sck]

#==============================================================================
# Clock Uncertainty (Setup includes jitter+margin; Hold includes post-CTS jitter)
#==============================================================================
set_clock_uncertainty -setup 0.500 [get_clocks clk_sys]
set_clock_uncertainty -hold  0.050 [get_clocks clk_sys]
set_clock_uncertainty -setup 1.000 [get_clocks clk_sck]
set_clock_uncertainty -hold  0.100 [get_clocks clk_sck]

#==============================================================================
# Clock Transition
#==============================================================================
set_clock_transition 0.2 [get_clocks clk_sys]

#==============================================================================
# Input Delays (relative to SCK clock domain for SPI inputs)
#==============================================================================

# CSB and MOSI are launched by the SPI master's SCK falling edge.
# We set input delay relative to clk_sck.
set_input_delay -max 10.0 -clock clk_sck [get_ports CSB]
set_input_delay -min 2.0  -clock clk_sck [get_ports CSB]

set_input_delay -max 10.0 -clock clk_sck [get_ports MOSI]
set_input_delay -min 2.0  -clock clk_sck [get_ports MOSI]

# SCK itself doesn't need input_delay since it's defined as a clock port.

#==============================================================================
# Output Delays
#==============================================================================

# MISO is driven by system clock logic but must meet SPI master's setup time
# relative to SCK.
set_output_delay -max 10.0 -clock clk_sck [get_ports MISO]
set_output_delay -min 2.0  -clock clk_sck [get_ports MISO]

#==============================================================================
# False Paths
#==============================================================================

# Asynchronous reset — no timing path
set_false_path -from [get_ports resetb]

# CDC synchronizer false paths:
# The 2-flop synchronizers handle metastability. The paths from async
# SPI inputs to the first flop stage are false paths in timing analysis.
# (The set_clock_groups directive above already covers SCK<->sys_clk crossings,
#  but we explicitly mark the synchronizer first-stage flops for clarity.)
#
# NOTE: Using wildcard patterns (*sync1*) instead of exact flop instance
# names. Genus may rename flops during synthesis (e.g., adding hierarchy
# prefixes or suffixes). Wildcards ensure these constraints survive renaming.
set_false_path -to [get_pins -hier *SCK_sync1*/D]
set_false_path -to [get_pins -hier *CSB_sync1*/D]
set_false_path -to [get_pins -hier *MOSI_sync1*/D]

#==============================================================================
# CDC Synchronizer Protection
# Prevent synthesis from optimizing away or merging synchronizer flops.
# This is MANDATORY for metastability protection in industry designs.
#==============================================================================
set_dont_touch [get_cells -hier *_sync1*]
set_dont_touch [get_cells -hier *_sync2*]

#==============================================================================
# Design Rule Constraints
#==============================================================================
set_max_fanout 20 [current_design]
set_max_transition 0.5 [current_design]
set_max_capacitance 0.5 [current_design]

#==============================================================================
# Driving Cell & Load (I/O pad modeling)
# Update cell names to match your PDK. These model realistic I/O conditions.
#==============================================================================
# set_driving_cell -lib_cell BUFX4 -pin Y [all_inputs]
# set_load 0.05 [all_outputs]

#==============================================================================
# Clock Network Latency (pre-CTS estimate)
# Gives synthesis a realistic clock arrival estimate before CTS.
# Remove or let Innovus override after CTS.
#==============================================================================
set_clock_latency -source 0.5 [get_clocks clk_sys]

#==============================================================================
# Area Optimization Target
#==============================================================================
# set_max_area 0  ;# Uncomment to push for minimum area

