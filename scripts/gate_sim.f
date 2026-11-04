// Gate-Level Simulation Script (Post-Synthesis Verification)
//
// PURPOSE: Re-run the same self-checking testbench against the gate-level
//          netlist produced by Genus. This catches synthesis bugs where the
//          tool may have incorrectly optimized or mapped logic.
//
// WHEN TO RUN: Immediately after Phase 3 (Genus Synthesis), before Phase 4.
//
// USAGE:
//   xrun -f scripts/gate_sim.f
//
// This is the EASIEST and most impactful verification you can add.
// If the gate-level sim passes the same tests as RTL sim, you have high
// confidence that synthesis preserved your design intent.

// Gate-level netlist from Genus (replaces RTL source)
netlist/spi_slave_synth.v

// Standard cell behavioral models (Verilog simulation models from 45nm GPDK)
/home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/verilog/fast_vdd1v0_basicCells.v
/home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/verilog/fast_vdd1v0_multibitsDFF.v

// Testbench (same as RTL simulation — no changes needed!)
tb/spi_slave_tb.v

// Simulation options
-64bit
-clean
-access +rwc
-timescale 1ns/1ps
-delay_mode zero
+notimingcheck
-run
