# Complete Industry-Grade RTL-to-GDSII ASIC Implementation Guide

A production-ready, step-by-step physical design and implementation handbook based on **Cadence Genus, Innovus, Conformal LEC, and PVS** using the **45nm GPDK (Generic Process Design Kit)** technology node.

---

## Table of Contents
1. [Flow Architecture & Design Overview](#1-flow-architecture--design-overview)
2. [Workspace Directory Structure & Prerequisites](#2-workspace-directory-structure--prerequisites)
3. [Step 0: RTL Architecture & Verification](#3-step-0-rtl-architecture--verification)
4. [Step 1: Timing Constraints (SDC)](#4-step-1-timing-constraints-sdc)
5. [Step 2: Logic Synthesis with Cadence Genus](#5-step-2-logic-synthesis-with-cadence-genus)
6. [Step 3: Formal Verification with Conformal LEC](#6-step-3-formal-verification-with-conformal-lec)
7. [Step 4: Multi-Mode Multi-Corner (MMMC) Setup](#7-step-4-multi-mode-multi-corner-mmmc-setup)
8. [Step 5: Physical Implementation with Cadence Innovus (PnR)](#8-step-5-physical-implementation-with-cadence-innovus-pnr)
   - [5.1 Initialization](#51-step-1-design-initialization)
   - [5.2 Floorplanning & Pin Placement](#52-step-2-floorplanning--pin-placement)
   - [5.3 Power Planning & Special Route (PDN)](#53-step-3-power-planning--power-routing)
   - [5.4 Standard Cell Placement & Pre-CTS Opt](#54-step-4-placement--pre-cts-optimization)
   - [5.5 Clock Tree Synthesis (CTS) with CCOpt](#55-step-5-clock-tree-synthesis-cts)
   - [5.6 Filler Cell Insertion](#56-step-6-filler-cell-insertion)
   - [5.7 Global & Detail Routing (NanoRoute)](#57-step-7-routing-nanoroute)
   - [5.8 Post-Route Hold Fixing & Optimization](#58-step-8-post-route-optimization--hold-fixing)
9. [Step 6: Parasitic Extraction (RC) & Timing Signoff](#9-step-6-parasitic-extraction--timing-signoff)
10. [Step 7: Physical Verification (DRC & LVS Signoff with Cadence PVS)](#10-step-7-physical-verification-pvs-drc--lvs)
11. [Step 8: Final GDSII Stream Out & Archival](#11-step-8-final-gdsii-stream-out--archival)
12. [Master Command Cheat Sheet & Debugging Playbook](#12-master-command-cheat-sheet--debugging-playbook)

---

## 1. Flow Architecture & Design Overview

The standard ASIC digital implementation flow translates high-level behavioral RTL (Verilog/VHDL) into physical manufacturing masks stored in **GDSII** stream format.

```
+-------------------------------------------------------------------------+
|                              RTL Design                                 |
|                 (Verilog-2001 / SystemVerilog: spi_slave.v)             |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                       Functional Verification                           |
|       (RTL Simulation: Xcelium / Icarus Verilog + Python cocotb)        |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  Logic Synthesis (Cadence Genus)                        |
|  Inputs: RTL (.v), Technology Libraries (.lib), Physical LEF, SDC       |
|  Outputs: Gate-Level Netlist (.v), Synthesized SDC, Area/Power/Timing   |
+-------------------------------------------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                                                       |
         v                                                       v
+------------------------------------+  +------------------------------------+
|  Formal Verification (Conformal)   |  | Gate-Level Simulation (GLS)        |
|  Golden (RTL) vs. Revised (Netlist)|  | Netlist + SDF timing simulation    |
+------------------------------------+  +------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  Place & Route (Cadence Innovus)                        |
|                                                                         |
|  1. Initialization (LEF, Netlist, MMMC setup: fast/slow corners)        |
|  2. Floorplanning (Core utilization, Aspect ratio, I/O pin placement)   |
|  3. Power Network (Core rings, VDD/VSS stripes, sroute standard rails)  |
|  4. Placement (Tap/endcap cells, timing-driven standard cell placement) |
|  5. Clock Tree Synthesis (CCOpt, target skew, latency balancing)        |
|  6. Filler Cell Insertion (N-well & active continuity)                  |
|  7. Routing (NanoRoute: global + track-assignment + detail routing)     |
|  8. Post-Route Optimization & Hold Fixing (Buffer insertion)           |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|               Parasitic Extraction & Signoff STA                        |
|  Engine: Innovus/Quantus Extractor -> SPEF (.spef) & SDF (.sdf)         |
|  STA: Static Timing Analysis with CPPR & OCV (Setup & Hold slack >= 0)  |
+-------------------------------------------------------------------------+
                                     |
         +---------------------------+---------------------------+
         |                                                       |
         v                                                       v
+------------------------------------+  +------------------------------------+
| Physical Verification (Cadence PVS)|  | Layout vs. Schematic (Cadence PVS) |
| DRC: Width, spacing, antenna rules |  | LVS: Netlist matching with CDL     |
+------------------------------------+  +------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                     Final GDSII Stream Out & Tapeout                    |
|             (output/spi_slave.gds via Foundry Layer Map File)           |
+-------------------------------------------------------------------------+
```

---

## 2. Workspace Directory Structure & Prerequisites

An organized directory structure prevents output collisions and streamlines automation scripts.

```text
semicom/
├── constraints/
│   └── spi_slave.sdc             # Synopsys Design Constraints file
├── src/
│   └── spi_slave.v               # Verilog-2001 synthesizable RTL
├── tb/
│   ├── spi_slave_tb.v            # Verilog testbench
│   └── verify_spi.py             # Python/cocotb functional verification
├── scripts/
│   ├── genus_synth.tcl           # Cadence Genus complete synthesis flow
│   ├── mmmc.tcl                  # Multi-Mode Multi-Corner timing views
│   ├── innovus_pnr.tcl           # Cadence Innovus end-to-end PnR flow
│   ├── conformal_lec.tcl         # Cadence Conformal LEC formal proof
│   ├── step1_init.tcl            # Modular Step 1: Design init
│   ├── step2_floorplan.tcl       # Modular Step 2: Floorplan & pins
│   ├── step3_power.tcl           # Modular Step 3: Rings, stripes, sroute
│   ├── step4_place.tcl           # Modular Step 4: Standard cell placement
│   ├── step5_cts.tcl             # Modular Step 5: CCOpt Clock tree synthesis
│   ├── step6_route.tcl           # Modular Step 6: NanoRoute & optimization
│   ├── step7_export.tcl          # Modular Step 7: GDSII, SPEF, SDF export
│   ├── step16_hold_fix.tcl       # Post-route hold ECO fix
│   ├── hcells.txt                # Hierarchy correspondence for LVS
│   ├── pvs_drc.ctrl              # PVS DRC control run file
│   ├── pvs_lvs.ctrl              # PVS LVS control run file
│   ├── run_pvs_drc.csh           # Shell script to invoke PVS DRC
│   └── run_pvs_lvs.csh           # Shell script to invoke PVS LVS
├── netlist/                      # Gate-level netlists & SDF/SPEF deliverables
├── reports/                      # Timing, area, power, DRC, LVS logs
├── output/                       # Output GDSII and Innovus session database (.enc)
└── pvs_output/                   # PVS signoff DRC and LVS run databases
```

### Foundry Reference Kit Paths (45nm GPDK SVT)
- **Standard Cell Timing Libraries (`.lib`)**:
  - Slow Corner (Worst): `slow_vdd1v0_basicCells.lib`
  - Fast Corner (Best): `fast_vdd1v0_basicCells.lib`
  - Typical Corner: `typical.lib`
- **Physical Layout Abstract (`.lef`)**:
  - Technology LEF: `gsclib045_tech.lef` (defines layers, vias, design rules, pitches)
  - Cell LEF: `gsclib045_macro.lef` (defines pin geometries, standard cell boundaries)
- **Physical Verification Rule Decks**:
  - DRC Rules: `pvlDRC.rul`
  - LVS Rules: `pvlLVS.rul`
  - Standard Cell SPICE/CDL: `gsclib045.cdl`
  - Stream Map: `gds2.map` (maps GDS layer/datatype numbers to Innovus metal layers)

---

## 3. Step 0: RTL Architecture & Verification

The example DUT is `spi_slave`—a synchronous 4-wire SPI Slave with internal register address mapping and Clock Domain Crossing (CDC) synchronizers.

### Key Architectural Features:
1. **Clock Domain Crossing (CDC)**: External asynchronous master signals (`SCK`, `CSB`, `MOSI`) are sampled by the internal 20 MHz system clock using two-stage flip-flop synchronizers to prevent metastability.
2. **One-Hot Finite State Machine (FSM)**:
   - `IDLE` (`6'b000001`): Waiting for `CSB` assertion (active low).
   - `FIRSTCYCLE` (`6'b000010`): Shifting in 8-bit command (bit[7]=R/W, bits[1:0]=address).
   - `WAITSECONDCYCLE` (`6'b000100`): Decoding command and preparing read data or write receiver.
   - `SECONDCYCLEWRITE` (`6'b001000`): Latching 8-bit incoming payload into internal registers.
   - `SECONDCYCLEREAD` (`6'b010000`): Transmitting 8-bit register data out on `MISO`.
   - `END` (`6'b100000`): Transaction completion handshake.
3. **Internal Registers**:
   - `0x00`: `decelerate`
   - `0x01`: `velocity`
   - `0x02`: `rotation`
   - `0x03`: `acceleration`

### Verilog Source Excerpt (`src/spi_slave.v`):
```verilog
module spi_slave (
    input  wire       clock,      // Internal system clock (e.g. 20 MHz)
    input  wire       resetb,     // Asynchronous active-low reset
    input  wire       SCK,        // External SPI serial clock
    input  wire       CSB,        // Chip Select (active-low)
    input  wire       MOSI,       // Master-Out Slave-In
    output reg        MISO        // Master-In Slave-Out
);
    // Double-flop synchronizers for asynchronous inputs
    reg SCK_sync1,  SCK_sync2;
    reg CSB_sync1,  CSB_sync2;
    reg MOSI_sync1, MOSI_sync2;

    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            SCK_sync1  <= 1'b0; SCK_sync2  <= 1'b0;
            CSB_sync1  <= 1'b1; CSB_sync2  <= 1'b1;
            MOSI_sync1 <= 1'b0; MOSI_sync2 <= 1'b0;
        end else begin
            SCK_sync1  <= SCK;  SCK_sync2  <= SCK_sync1;
            CSB_sync1  <= CSB;  CSB_sync2  <= CSB_sync1;
            MOSI_sync1 <= MOSI; MOSI_sync2 <= MOSI_sync1;
        end
    end
    // ... FSM and data registers ...
endmodule
```

### Verification Command:
```bash
# Run RTL simulation using Icarus Verilog or Cadence Xcelium
iverilog -o sim_spi tb/spi_slave_tb.v src/spi_slave.v
vvp sim_spi
```

---

## 4. Step 1: Timing Constraints (SDC)

The Synopsys Design Constraints file (`constraints/spi_slave.sdc`) dictates the clock frequencies, margins, and I/O budgets for synthesis and physical implementation.

### Complete SDC (`constraints/spi_slave.sdc`):
```tcl
###############################################################################
# SDC Constraints for spi_slave
###############################################################################

# 1. Clocks
# System clock: 20 MHz -> 50 ns period
create_clock -name clk_sys -period 50.0 [get_ports clock]

# SPI clock: 2 MHz -> 500 ns period
create_clock -name clk_sck -period 500.0 [get_ports SCK]

# 2. Clock Domain Crossing (Asynchronous Clocks)
# clk_sys and clk_sck are mutually asynchronous
set_clock_groups -asynchronous \
    -group [get_clocks clk_sys] \
    -group [get_clocks clk_sck]

# 3. Clock Uncertainty (Jitter, Skew Margin)
set_clock_uncertainty -setup 0.500 [get_clocks clk_sys]
set_clock_uncertainty -hold  0.050 [get_clocks clk_sys]
set_clock_uncertainty -setup 1.000 [get_clocks clk_sck]
set_clock_uncertainty -hold  0.100 [get_clocks clk_sck]

# 4. Clock Transition
set_clock_transition 0.2 [get_clocks clk_sys]

# 5. Input Delays (Delays from external SPI master launcher)
set_input_delay -max 10.0 -clock clk_sck [get_ports CSB]
set_input_delay -min  2.0 -clock clk_sck [get_ports CSB]
set_input_delay -max 10.0 -clock clk_sck [get_ports MOSI]
set_input_delay -min  2.0 -clock clk_sck [get_ports MOSI]

# 6. Output Delays
set_output_delay -max 10.0 -clock clk_sck [get_ports MISO]
set_output_delay -min  2.0 -clock clk_sck [get_ports MISO]

# 7. Environmental Constraints (Drive strength & Load)
# Assume standard inverter driving inputs and 20 fF capacitive load on outputs
set_load -pin_load 0.020 [get_ports MISO]
```

---

## 5. Step 2: Logic Synthesis with Cadence Genus

Logic synthesis transforms RTL constructs into a generic logic representation (GTECH), maps them to targeted standard cells, and optimizes for setup timing, total area, and dynamic power.

### Execution Command:
```bash
genus -f scripts/genus_synth.tcl
```

### Complete Synthesis Script (`scripts/genus_synth.tcl`):
```tcl
###############################################################################
# Cadence Genus Synthesis Script
###############################################################################

# 1. Output Directories
file mkdir reports
file mkdir netlist

# 2. Setup Search Paths & Technology Libraries
set_db / .init_lib_search_path {
    /home/ec/install/FOUNDRY/digital/45nm/dig/lib
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing
}
set_db / .init_hdl_search_path {./src}

# Target .lib for synthesis mapping
set_db / .library {/home/ec/install/FOUNDRY/digital/45nm/dig/lib/typical.lib}

# Physical LEF for wire-load & area estimation
set_db / .lef_library {
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/lef/gsclib045_macro.lef
}

# 3. Read RTL & Elaborate
read_hdl -verilog src/spi_slave.v
elaborate spi_slave

# Check elaboration integrity
check_design -unresolved

# 4. Read Timing Constraints
read_sdc constraints/spi_slave.sdc
report_clocks > reports/clocks_synth.rpt

# 5. Three-Stage Synthesis
# Stage A: Generic synthesis (RTL -> GTECH)
syn_generic

# Stage B: Technology Mapping (GTECH -> 45nm standard cell gates)
syn_map

# Stage C: Logic Optimization (Timing, Area, Power)
syn_opt

# 6. Quality of Results (QoR) Reporting
check_design -all          > reports/check_design_synth.rpt
check_timing_intent        > reports/check_timing_intent.rpt
report_timing -nworst 10   > reports/timing_synth.rpt
report_timing              > reports/timing_setup_synth.rpt
report_area                > reports/area_synth.rpt
report_power               > reports/power_synth.rpt
report_gates               > reports/gates_synth.rpt
report_qor                 > reports/qor_synth.rpt

# 7. Export Gate-Level Netlist & SDC for Place & Route
write_hdl                  > netlist/spi_slave_synth.v
write_sdc                  > netlist/spi_slave_synth.sdc
puts "=== Genus Synthesis Completed Successfully ==="
```

### Signoff Criteria for Synthesis:
- [x] **Zero Unresolved Modules/Blackboxes**: `check_design -unresolved` returns 0.
- [x] **Setup Slack Positive**: Slack in `reports/timing_synth.rpt` must be $\ge 0.00\text{ ps}$.
- [x] **No Undriven Nets**: Verified via `reports/check_design_synth.rpt`.

---

## 6. Step 3: Formal Verification with Conformal LEC

Formal Logic Equivalence Checking (LEC) compares the golden RTL source directly against the gate-level synthesized netlist using mathematical solvers. No test vectors are needed.

### Execution Command:
```bash
lec -xl -nogui -do scripts/conformal_lec.tcl
```

### Complete LEC Script (`scripts/conformal_lec.tcl`):
```tcl
###############################################################################
# Cadence Conformal LEC Script
###############################################################################
set_log_file lec_results.log -replace

# Enable sequential optimization mapping
set_flatten_model -seq_constant -all
set_flatten_model -nodeset_to_constraint

# 1. Read Golden Library & RTL
read_library -liberty /home/ec/install/FOUNDRY/digital/45nm/dig/lib/typical.lib -both
read_design src/spi_slave.v -verilog -golden -lastmod -norangeconstraint
set_root_module spi_slave -golden

# 2. Read Revised Design (Synthesized Gate Netlist)
read_design netlist/spi_slave_synth.v -verilog -revised -lastmod -norangeconstraint
set_root_module spi_slave -revised

# 3. Apply Matching Constraints
add_pin_constraint 1 resetb -golden
add_pin_constraint 1 resetb -revised

# 4. Map Compare Points (Registers, Latches, Outputs)
set_system_mode lec
map_key_points
report_unmapped_points

# 5. Execute Mathematical Comparison
add_compare_points -all
compare

# 6. Verify Results
report_compare_data -nonequivalent
puts "=== Formal Verification Proof Complete ==="
```
> **Goal**: Output must report `Compared points: N, Equivalent: N, Non-equivalent: 0`.

---

## 7. Step 4: Multi-Mode Multi-Corner (MMMC) Setup

Physical implementation requires concurrent optimization across process, voltage, and temperature extremes:
- **Setup Corner**: Slow Process, Low VDD ($1.0\text{ V}$), High Temp ($125^\circ\text{C}$).
- **Hold Corner**: Fast Process, High VDD ($1.0\text{ V}$), Low Temp ($0^\circ\text{C}$).

### Complete MMMC File (`scripts/mmmc.tcl`):
```tcl
###############################################################################
# Cadence Innovus MMMC Configuration (45nm GPDK)
###############################################################################

# 1. Library Sets
create_library_set -name slow_libs -timing {
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/slow_vdd1v0_basicCells.lib
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/slow_vdd1v0_multibitsDFF.lib
}

create_library_set -name fast_libs -timing {
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/fast_vdd1v0_basicCells.lib
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/timing/fast_vdd1v0_multibitsDFF.lib
}

# 2. RC Interconnect Corners
create_rc_corner -name slow_rc -temperature 125
create_rc_corner -name fast_rc -temperature 0

# 3. Delay Corners
create_delay_corner -name slow_delay -library_set slow_libs -rc_corner slow_rc
create_delay_corner -name fast_delay -library_set fast_libs -rc_corner fast_rc

# 4. Constraint Mode (Sourced from Genus exported SDC)
create_constraint_mode -name func_mode -sdc_files {netlist/spi_slave_synth.sdc}

# 5. Analysis Views
create_analysis_view -name slow_view -constraint_mode func_mode -delay_corner slow_delay
create_analysis_view -name fast_view -constraint_mode func_mode -delay_corner fast_delay

# 6. View Assignments: Setup uses Slow Corner, Hold uses Fast Corner
set_analysis_view -setup {slow_view} -hold {fast_view}
```

---

## 8. Step 5: Physical Implementation with Cadence Innovus (PnR)

Place and Route (PnR) transforms the gate netlist into a fully routed, DRC/LVS-clean physical layout.

You can run the complete batch flow with:
```bash
innovus -stylus -f scripts/innovus_pnr.tcl
```
*(Or launch Innovus interactively with `innovus` and source individual step scripts).*

Below are the detailed, annotated steps executed during PnR:

---

### 5.1 Step 1: Design Initialization
Initializes the tool with physical geometry definitions, logical gates, and timing constraints.

```tcl
# Create clean directory structure
file mkdir reports reports/preCTS reports/postCTS reports/postCTS_hold
file mkdir reports/postRoute reports/postRoute_hold reports/signoff
file mkdir output netlist pvs_output/drc pvs_output/lvs

catch {freeDesign}

# Read MMMC configuration
read_mmmc scripts/mmmc.tcl

# Read Physical Layout Abstract (LEF)
read_physical -lefs {
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef
    /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/lef/gsclib045_macro.lef
}

# Read synthesized netlist
read_netlist netlist/spi_slave_synth.v -top spi_slave

# Initialize design database
init_design
```

---

### 5.2 Step 2: Floorplanning & Pin Placement
Defines the die and core boundaries, standard cell rows, and input/output pin assignments on specific metal layers.

```tcl
# Define Core: Aspect Ratio = 1.0 (Square), 65% target utilization
# Margins: Left=10um, Bottom=10um, Right=10um, Top=10um
floorPlan -r 1.0 0.65 10 10 10 10

# Align external I/O pins to Metal3 to prevent congestion on lower layers
editPin -side North -pin {clock resetb} -layer Metal3
editPin -side East  -pin {MISO}         -layer Metal3
editPin -side West  -pin {SCK CSB MOSI} -layer Metal3

# Check floorplan legality
checkPinAssignment
```

---

### 5.3 Step 3: Power Planning & Power Routing
Designs the Power Delivery Network (PDN) to minimize IR drop and supply clean $V_{DD}$ and $V_{SS}$ across the entire die.

```tcl
# 1. Connect Logical PG Pins to Global Power & Ground Nets
globalNetConnect VDD -type pgpin -pin VDD -inst * -all
globalNetConnect VSS -type pgpin -pin VSS -inst * -all

# 2. Add Core Power Rings (Low-resistance ring around standard cell area)
addRing -type core_rings \
    -nets {VDD VSS} \
    -layer {top Metal5 bottom Metal5 left Metal4 right Metal4} \
    -width 1.5 -spacing 0.5 -offset 2.0

# 3. Add Power Stripes (Vertical on Metal5, Horizontal on Metal4)
addStripe -nets {VDD VSS} \
    -layer Metal5 -direction vertical \
    -width 1.0 -spacing 0.5 -set_to_set_distance 40 \
    -start_from left -start_offset 10

addStripe -nets {VDD VSS} \
    -layer Metal4 -direction horizontal \
    -width 1.0 -spacing 0.5 -set_to_set_distance 40 \
    -start_from bottom -start_offset 10

# 4. Special Route (sroute): Connect Standard Cell Power Rails (Metal1 follow-pins)
sroute -connect {blockPin padPin corePin} \
    -layerChangeRange {Metal1 Metal5} \
    -blockPinTarget nearestTarget \
    -padPinPortConnect allPort \
    -allowJogging 1 \
    -allowLayerChange 1 \
    -nets {VDD VSS}
```

---

### 5.4 Step 4: Placement & Pre-CTS Optimization
Places standard cells into standard cell rows with timing-driven clustering and wire-length minimization.

```tcl
# 1. Insert Endcap and Well-Tap cells (Prevents latch-up by biasing wells)
catch {addEndCap -prefix ENDCAP}
catch {addWellTap -cell FILL1 -cellInterval 30 -prefix WELLTAP}
catch {addWellTap -cell WELLTAP -cellInterval 30 -prefix WELLTAP}

# 2. Timing-Driven Standard Cell Placement & Optimization
place_opt_design

# 3. Check Placement Legality (Overlap detection)
checkPlace

# 4. Report Pre-CTS Setup Timing
timeDesign -preCTS -outDir reports/preCTS
```

---

### 5.5 Step 5: Clock Tree Synthesis (CTS)
Synthesizes balanced clock trees using Cadence CCOpt (Clock Concurrent Optimization) to minimize clock skew and transition times.

```tcl
# 1. Specify CTS buffer and inverter driving cells
catch {set_ccopt_property buffer_cells {CLKBUFX2 CLKBUFX4 CLKBUFX8 BUFX2 BUFX4 BUFX8}}
catch {set_ccopt_property inverter_cells {CLKINVX1 CLKINVX2 CLKINVX4 INVX1 INVX2 INVX4}}

# 2. Target Skew (100 ps) and Max Transition (300 ps)
set_ccopt_property target_max_trans 0.3
set_ccopt_property target_skew 0.1

# 3. Generate & Source CCOpt Clock Tree Spec
create_ccopt_clock_tree_spec -file ccopt.spec
source ccopt.spec

# 4. Run Clock Tree Synthesis
ccopt_design -cts

# 5. Post-CTS Optimization (Hold & Setup)
timeDesign -postCTS -outDir reports/postCTS
optDesign  -postCTS
optDesign  -postCTS -hold
timeDesign -postCTS -hold -outDir reports/postCTS_hold
```

---

### 5.6 Step 6: Filler Cell Insertion
Standard cell rows have empty gaps where no logic exists. **Filler cells** must be inserted to ensure N-well continuity, substrate tap continuity, and poly layer planarity before routing.

```tcl
# Insert non-functional filler cells from largest to smallest
catch {
    addFiller -cell {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1} -prefix FILLER
}

# Verify no layout voids remain
checkPlace
```

---

### 5.7 Step 7: Routing (NanoRoute)
Performs grid-based global routing, track assignment, and detail routing using Cadence NanoRoute.

```tcl
# Execute detail routing
routeDesign

# Enable On-Chip Variation (OCV) analysis with Clock Path Pessimism Removal (CPPR)
setAnalysisMode -analysisType onChipVariation -cppr both

# Post-route timing optimization
optDesign -postRoute
optDesign -postRoute -hold

# Post-route timing verification
timeDesign -postRoute      -outDir reports/postRoute
timeDesign -postRoute -hold -outDir reports/postRoute_hold
```

---

### 5.8 Step 8: Post-Route Optimization & Hold Fixing
If post-route STA reveals remaining hold violations (common when clock skew is small and data paths are short), perform buffer-insertion ECO:

```tcl
# Sourced from scripts/step16_hold_fix.tcl:
puts "--> Removing filler cells for ECO buffer insertion..."
catch {deleteFiller}

# Configure Hold Optimization
setOptMode -fixHoldAllowSetupTnsDegrade false
setOptMode -holdTargetSlack 0.020
setOptMode -addInstancePrefix HOLD_BUF_
catch {setOptMode -holdFixingCells {DLY1X1 DLY1X4 DLY2X1 DLY2X4 BUFX2 BUFX3 BUFX4}}

# Fix hold violations
catch {optDesign -postRoute -hold}

# Route newly inserted ECO nets
catch {ecoRoute}

# Re-insert filler cells
catch {addFiller -cell {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1} -prefix FILLER}
```

---

## 9. Step 6: Parasitic Extraction (RC) & Timing Signoff

Extracts resistance and capacitance of all interconnect wires into **SPEF** and writes out **SDF** for gate-level back-annotated timing simulation.

```tcl
# 1. Signoff Parasitic Extraction
setExtractRCMode -engine postRoute -effortLevel signoff
extractRC

# 2. Write out SPEF file
rcOut -spef netlist/spi_slave_postroute.spef

# 3. Write out Standard Delay Format (SDF v3.0)
write_sdf -version 3.0 netlist/spi_slave_postroute.sdf

# 4. Final Signoff Static Timing Analysis
timeDesign -signoff      -outDir reports/signoff
timeDesign -signoff -hold -outDir reports/signoff_hold

# 5. Export Post-Route Netlists
# Logical Netlist (for LEC and GLS)
saveNetlist netlist/spi_slave_postroute.v

# Netlist with Power & Ground pins (Required for PVS LVS Signoff)
saveNetlist -includePowerGround netlist/spi_slave_postroute_pg.v
```

---

## 10. Step 7: Physical Verification (PVS DRC & LVS)

Physical signoff ensures the layout conforms strictly to foundry manufacturing rules (DRC) and matches the logical netlist perfectly (LVS).

### 10.1 Cadence PVS DRC (Design Rule Checking)
Validates minimum metal widths, metal-to-metal spacing, via overlap, enclosure, and antenna rules.

#### Run Command:
```csh
./scripts/run_pvs_drc.csh
```
*Script content:*
```csh
#!/bin/csh -f
mkdir -p pvs_output/drc
pvs -drc \
  -gds output/spi_slave.gds \
  -top_cell spi_slave \
  -run_dir pvs_output/drc \
  /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlDRC.rul
```
Check `pvs_output/drc/spi_slave.sum` for **Total DRC Violations: 0**.

---

### 10.2 Cadence PVS LVS (Layout Versus Schematic)
Extracts transistors and metal connectivity from the GDSII and compares them against the gate netlist + foundry transistor CDL.

#### Run Command:
```csh
./scripts/run_pvs_lvs.csh
```
*Script content:*
```csh
#!/bin/csh -f
mkdir -p pvs_output/lvs
pvs -lvs \
  -automatch \
  -hcell scripts/hcells.txt \
  -gds output/spi_slave.gds \
  -top_cell spi_slave \
  -source_top_cell spi_slave \
  -source_verilog netlist/spi_slave_postroute_pg.v \
  -source_cdl /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs/GPDK045/gsclib045_svt_v4.4/gsclib045/cdl/gsclib045.cdl \
  -control scripts/pvs_lvs.ctrl \
  -run_dir pvs_output/lvs \
  /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlLVS.rul
```
Check `pvs_output/lvs/spi_slave.rep`. Signoff requires:
```text
#####################################################################
###                  LVS STATUS: CORRECT                          ###
###          LAYOUT AND SOURCE NETLIST ARE EQUIVALENT             ###
#####################################################################
```

---

## 11. Step 8: Final GDSII Stream Out & Archival

The final physical layout is streamed out to **GDSII** format using the foundry layer map file.

### GDSII Export Script (`scripts/step7_export.tcl`):
```tcl
###############################################################################
# Stream Out GDSII
###############################################################################

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

# Save Innovus Design Database for Future ECOs / Resumption
saveDesign output/spi_slave_final.enc

puts "========================================================"
puts "=== GDSII STREAM-OUT COMPLETE: output/spi_slave.gds ==="
puts "========================================================"
```

---

## 12. Master Command Cheat Sheet & Debugging Playbook

### Master Execution Commands

| Stage | Tool | Command Line |
|---|---|---|
| **1. RTL Simulation** | Xcelium / Icarus | `iverilog -o sim tb/spi_slave_tb.v src/spi_slave.v && vvp sim` |
| **2. Logic Synthesis** | Cadence Genus | `genus -f scripts/genus_synth.tcl` |
| **3. Formal Verification**| Cadence Conformal | `lec -xl -nogui -do scripts/conformal_lec.tcl` |
| **4. Place & Route** | Cadence Innovus | `innovus -stylus -f scripts/innovus_pnr.tcl` |
| **5. Signoff DRC** | Cadence PVS | `csh scripts/run_pvs_drc.csh` |
| **6. Signoff LVS** | Cadence PVS | `csh scripts/run_pvs_lvs.csh` |

---

### Common Physical Design Issues & Fixes

#### 1. Setup Violations (Negative Slack at Pre-CTS / Post-Route)
- **Root Cause**: High combinational logic depth, high fanout nets, or low-drive cell selection.
- **Fix**:
  ```tcl
  setOptMode -effort high
  optDesign -postRoute -setup
  ```
  Check `report_timing -nworst 5` to locate the critical path.

#### 2. Hold Violations (Data arrives before Clock Hold Edge)
- **Root Cause**: Clock skew between launch and capture flops; fast data path (inverters/buffers).
- **Fix**: Run buffer insertion ECO with delay cells:
  ```tcl
  deleteFiller
  setOptMode -holdTargetSlack 0.050 -holdFixingCells {DLY1X1 DLY2X1 BUFX2}
  optDesign -postRoute -hold
  ecoRoute
  addFiller -cell {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1} -prefix FILLER
  ```

#### 3. Power Rail Disconnects (`verifyConnectivity` fails)
- **Root Cause**: Missing `sroute` connection between standard cell Metal1 rails and core rings/stripes.
- **Fix**:
  ```tcl
  globalNetConnect VDD -type pgpin -pin VDD -inst * -all
  globalNetConnect VSS -type pgpin -pin VSS -inst * -all
  sroute -connect {blockPin padPin corePin} -layerChangeRange {Metal1 Metal5} -nets {VDD VSS}
  ```

#### 4. LVS Mismatch (Power / Ground Pins Missing)
- **Root Cause**: Running LVS against logical Verilog (`saveNetlist file.v`) rather than physical PG netlist (`saveNetlist -includePowerGround file_pg.v`).
- **Fix**: Always pass `-includePowerGround` for LVS netlist exports and ensure `hcells.txt` maps all standard cell gates.

---
*Created as part of the production-level 45nm ASIC Physical Design Flow.*

