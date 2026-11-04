# ####################################################################

#  Created by Genus(TM) Synthesis Solution 21.14-s082_1 on Thu Oct 15 00:57:05 AKDT 2026

# ####################################################################

set sdc_version 2.0

set_units -capacitance 1000fF
set_units -time 1000ps

# Set the current design
current_design spi_slave

create_clock -name "clk_sys" -period 50.0 -waveform {0.0 25.0} [get_ports clock]
create_clock -name "clk_sck" -period 500.0 -waveform {0.0 250.0} [get_ports SCK]
set_clock_transition 0.2 [get_clocks clk_sys]
set_false_path -from [get_ports resetb]
set_false_path -to [list \
  [get_pins SCK_sync1_reg/D]  \
  [get_pins CSB_sync1_reg/D]  \
  [get_pins MOSI_sync1_reg/D] ]
set_clock_groups -name "clock_groups_clk_sys_to_clk_sck" -asynchronous -group [get_clocks clk_sys] -group [get_clocks clk_sck]
set_clock_gating_check -setup 0.0 
set_input_delay -clock [get_clocks clk_sck] -add_delay -max 10.0 [get_ports CSB]
set_input_delay -clock [get_clocks clk_sck] -add_delay -min 2.0 [get_ports CSB]
set_input_delay -clock [get_clocks clk_sck] -add_delay -max 10.0 [get_ports MOSI]
set_input_delay -clock [get_clocks clk_sck] -add_delay -min 2.0 [get_ports MOSI]
set_output_delay -clock [get_clocks clk_sck] -add_delay -max 10.0 [get_ports MISO]
set_output_delay -clock [get_clocks clk_sck] -add_delay -min 2.0 [get_ports MISO]
set_max_fanout 20.000 [current_design]
set_max_transition 0.5 [current_design]
set_max_capacitance 0.5 [current_design]
set_clock_latency -source 0.5 [get_clocks clk_sys]
set_clock_uncertainty -setup 0.5 [get_clocks clk_sys]
set_clock_uncertainty -hold 0.5 [get_clocks clk_sys]
set_clock_uncertainty -setup 1.0 [get_clocks clk_sck]
set_clock_uncertainty -hold 1.0 [get_clocks clk_sck]
