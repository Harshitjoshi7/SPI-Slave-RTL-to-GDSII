if {![namespace exists ::IMEX]} { namespace eval ::IMEX {} }
set ::IMEX::dataVar [file dirname [file normalize [info script]]]
set ::IMEX::libVar ${::IMEX::dataVar}/libs

create_library_set -name fast_libs\
   -timing\
    [list ${::IMEX::libVar}/mmmc/fast_vdd1v0_basicCells.lib\
    ${::IMEX::libVar}/mmmc/fast_vdd1v0_multibitsDFF.lib]
create_library_set -name slow_libs\
   -timing\
    [list ${::IMEX::libVar}/mmmc/slow_vdd1v0_basicCells.lib\
    ${::IMEX::libVar}/mmmc/slow_vdd1v0_multibitsDFF.lib]
create_rc_corner -name slow_rc\
   -preRoute_res 1\
   -postRoute_res 1\
   -preRoute_cap 1\
   -postRoute_cap 1\
   -postRoute_xcap 1\
   -preRoute_clkres 0\
   -preRoute_clkcap 0
create_rc_corner -name fast_rc\
   -preRoute_res 1\
   -postRoute_res 1\
   -preRoute_cap 1\
   -postRoute_cap 1\
   -postRoute_xcap 1\
   -preRoute_clkres 0\
   -preRoute_clkcap 0
create_delay_corner -name slow_delay\
   -library_set slow_libs\
   -rc_corner slow_rc
create_delay_corner -name fast_delay\
   -library_set fast_libs\
   -rc_corner fast_rc
create_constraint_mode -name func_mode\
   -sdc_files\
    [list /dev/null]
create_analysis_view -name fast_view -constraint_mode func_mode -delay_corner fast_delay
create_analysis_view -name slow_view -constraint_mode func_mode -delay_corner slow_delay
set_analysis_view -setup [list slow_view] -hold [list fast_view]
