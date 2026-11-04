###############################################################################
# SDC Constraints: and_gate
# Note: Pure combinational – only I/O delays defined, no clock required.
###############################################################################

# Virtual clock for I/O timing budget (100 MHz reference)
create_clock -name vclk -period 10.0

# Input arrival times
set_input_delay  -max 2.0 -clock vclk [get_ports {a b}]
set_input_delay  -min 0.5 -clock vclk [get_ports {a b}]

# Output required times
set_output_delay -max 2.0 -clock vclk [get_ports y]
set_output_delay -min 0.5 -clock vclk [get_ports y]

# Drive strength of inputs (typical std cell inverter: INVX1)
set_driving_cell -lib_cell INVX1 [get_ports {a b}]

# Output load (20 fF)
set_load -pin_load 0.020 [get_ports y]

