# 🚀 4-Wire Synchronous SPI Slave: Complete RTL-to-GDSII ASIC Flow (45nm GPDK)

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Technology](https://img.shields.io/badge/Node-45nm%20GPDK-green.svg)](#)
[![Tools](https://img.shields.io/badge/EDA-Cadence%20Xcelium%20|%20Genus%20|%20Innovus%20|%20Conformal%20|%20PVS-red.svg)](#)
[![Signoff](https://img.shields.io/badge/Signoff-DRC%20Clean%20|%20LVS%20Match-brightgreen.svg)](#)

A complete, production-grade digital ASIC implementation of a **4-wire synchronous SPI Slave core** with Clock Domain Crossing (CDC) synchronizers, command decoder FSM, and internal register bank, carried out from synthesizable Verilog RTL to clean **GDSII** stream-out using the **Cadence Digital Implementation Flow** on **45nm GPDK (Generic Process Design Kit)** standard cells.

---

## 📑 Table of Contents
- [Architecture & Design Specifications](#-architecture--design-specifications)
- [Project Directory Structure](#-project-directory-structure)
- [ASIC Implementation Flow](#-asic-implementation-flow)
- [1. RTL Simulation & Verification](#1-rtl-simulation--verification)
- [2. Logic Synthesis (Cadence Genus)](#2-logic-synthesis-cadence-genus)
- [3. Formal Equivalence Checking (Conformal LEC)](#3-formal-equivalence-checking-conformal-lec)
- [4. Place & Route (Cadence Innovus)](#4-place--route-cadence-innovus)
- [5. Physical Signoff (Cadence PVS DRC & LVS)](#5-physical-signoff-cadence-pvs-drc--lvs)
- [Physical Layout & Verification Gallery](#-physical-layout--verification-gallery)
- [Quick Start Command Playbook](#-quick-start-command-playbook)
- [Author & Acknowledgments](#-author--acknowledgments)

---

## 📐 Architecture & Design Specifications

The core is a configurable **SPI Slave** peripheral supporting **SPI Mode 0** ($\text{CPOL}=0, \text{CPHA}=0$):
- **System Clock Domain**: $20\text{ MHz}$ ($50\text{ ns}$ period) internal clock domain.
- **SPI Interface Clock Domain**: Up to $2\text{ MHz}$ ($500\text{ ns}$ period) external `SCK`.
- **Clock Domain Crossing (CDC)**: 2-stage DFF synchronizers on all asynchronous inputs (`SCK`, `CSB`, `MOSI`) with edge-detection logic in the system clock domain to eliminate metastability.
- **Control FSM**: One-hot encoded state machine (`IDLE`, `FIRSTCYCLE`, `WAITSECONDCYCLE`, `SECONDCYCLEWRITE`, `SECONDCYCLEREAD`, `END`).
- **Register Bank**: Four 8-bit memory-mapped control and telemetry registers:
  - `0x00`: `decelerate`
  - `0x01`: `velocity`
  - `0x02`: `rotation`
  - `0x03`: `acceleration`

### Pinout Description
| Port Name | Direction | Clock Domain | Description |
|---|---|---|---|
| `clock` | Input | System ($20\text{ MHz}$) | Primary core system clock |
| `resetb` | Input | Asynchronous | Active-low asynchronous reset |
| `SCK` | Input | SPI ($2\text{ MHz}$) | Serial clock from external SPI Master |
| `CSB` | Input | SPI | Active-low chip select from Master |
| `MOSI` | Input | SPI | Master-Out-Slave-In serial data line |
| `MISO` | Output | System / SPI | Master-In-Slave-Out serial data line |

---

## 📂 Project Directory Structure

```text
├── constraints/
│   └── spi_slave.sdc              # Timing constraints (SDC 2.1)
├── src/
│   └── spi_slave.v                # Synthesizable RTL Verilog source
├── tb/
│   ├── spi_slave_tb.v             # Comprehensive self-checking testbench
│   └── verify_spi.py              # Python / cocotb test verification
├── scripts/
│   ├── genus_synth.tcl            # Cadence Genus complete synthesis flow
│   ├── mmmc.tcl                   # Multi-Mode Multi-Corner definition
│   ├── innovus_pnr.tcl            # Cadence Innovus end-to-end PnR flow
│   ├── conformal_lec.tcl          # Cadence Conformal formal equivalence proof
│   ├── step1_init.tcl             # Step 1: Design database initialization
│   ├── step2_floorplan.tcl        # Step 2: Floorplan, core utilization, pin placement
│   ├── step3_power.tcl            # Step 3: Power rings, stripes, and follow-pin sroute
│   ├── step4_place.tcl            # Step 4: Endcap, well-tap, timing-driven placement
│   ├── step5_cts.tcl              # Step 5: CCOpt clock tree synthesis & balance
│   ├── step6_route.tcl            # Step 6: Filler cell insertion & NanoRoute
│   ├── step7_export.tcl           # Step 7: GDSII, SPEF, SDF, netlist export
│   ├── step16_hold_fix.tcl        # Post-route hold violation ECO buffer insertion
│   ├── hcells.txt                 # Hierarchy correspondence file for PVS LVS
│   ├── pvs_drc.ctrl               # PVS DRC control rule options
│   ├── pvs_lvs.ctrl               # PVS LVS control rule options
│   ├── run_pvs_drc.csh            # Shell execution script for PVS DRC
│   └── run_pvs_lvs.csh            # Shell execution script for PVS LVS
├── project_spi_images/            # Tool screenshots (Genus, Innovus, PVS DRC/LVS)
├── RTL_TO_GDSII_COMPLETE_GUIDE.md # Detailed technical manual & command guide
└── .gitignore                     # Git ignore rules for Cadence temp/log files
```

---

## 🔄 ASIC Implementation Flow

```
                      +-----------------------------+
                      |   Synthesizable RTL Verilog |
                      |       (src/spi_slave.v)     |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |   RTL Simulation (xrun)     |
                      |     (tb/spi_slave_tb.v)     |
                      +-----------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Logic Synthesis (Genus)    |
                      |  - Target: 45nm GPDK SVT    |
                      |  - SDC: 20 MHz sys, 2MHz SPI|
                      +-----------------------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+-------------------------+                     +-------------------------+
| Formal LEC (Conformal)  |                     |  Gate-Level Simulation  |
| Golden RTL vs. Netlist  |                     |  (netlist/spi_slave.v)  |
+-------------------------+                     +-------------------------+
             |
             v
+-------------------------------------------------------------------------+
|                  Physical Implementation (Cadence Innovus)              |
|                                                                         |
|  1. MMMC & Library Initialization (slow_vdd1v0 @ 125C, fast @ 0C)       |
|  2. Floorplanning (Core Util: 65%, Aspect Ratio: 1.0, Metal3 I/O pins)  |
|  3. Power Delivery Network (Core Rings, Metal4/5 Stripes, M1 sroute)   |
|  4. Standard Cell Placement (Well-taps @ 30um, Endcaps, place_opt)     |
|  5. Clock Tree Synthesis (CCOpt, target skew: 100ps, max trans: 300ps) |
|  6. Filler Cell Insertion (FILL64..FILL1 for N-well/active continuity)  |
|  7. Routing (NanoRoute: Global + Detail routing with OCV & CPPR)       |
|  8. Post-Route Timing Optimization & Hold ECO Fix                       |
+-------------------------------------------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  Parasitic Extraction & Signoff STA                     |
|  - Signoff RC extraction -> SPEF & SDF generation                       |
|  - Static Timing Analysis across setup & hold corners                   |
+-------------------------------------------------------------------------+
                                     |
             +-----------------------+-----------------------+
             |                                               |
             v                                               v
+-------------------------+                     +-------------------------+
|   Cadence PVS Signoff   |                     |   Cadence PVS Signoff   |
|     Design Rule Check   |                     |   Layout vs. Schematic  |
|         (DRC: 0)        |                     |     (LVS: Equivalent)   |
+-------------------------+                     +-------------------------+
                                     |
                                     v
                      +-----------------------------+
                      |     Tapeout GDSII Stream    |
                      |    (output/spi_slave.gds)   |
                      +-----------------------------+
```

---

## 1. RTL Simulation & Verification

Simulation is verified using **Cadence Xcelium (`xrun`)**:
```bash
# RTL Simulation with Cadence Xcelium
xrun -64bit -clean -timescale 1ns/1ps -access +rwc src/spi_slave.v tb/spi_slave_tb.v -log reports/xrun_rtl.log
```
The testbench validates:
1. Multi-register write transactions across address spaces `0x00` through `0x03`.
2. Serial readback and byte comparison.
3. Overwrite verification and boundary condition assertions (`0x00`, `0xFF`).
4. Mid-transaction `CSB` aborts for robustness and state-recovery verification.

---

## 2. Logic Synthesis (Cadence Genus)

Synthesis maps RTL logic into the **GPDK045** standard cell library:
```bash
genus -f scripts/genus_synth.tcl
```
- **Constraint Strategy**: Defined in `constraints/spi_slave.sdc` using asynchronous clock groups (`set_clock_groups -asynchronous`) between `clk_sys` and `clk_sck`.
- **Results**: Zero unresolved references, positive slack on all paths, optimized area and dynamic power consumption.

---

## 3. Formal Equivalence Checking (Conformal LEC)

Proves that technology-mapped gates preserve exact functional intent without test vectors:
```bash
lec -xl -nogui -do scripts/conformal_lec.tcl
```
- **Golden**: `src/spi_slave.v`
- **Revised**: `netlist/spi_slave_synth.v`
- **Result**: `Compared points: N, Equivalent: N, Non-equivalent: 0` (100% equivalence).

---

## 4. Place & Route (Cadence Innovus)

Physical design implements the layout inside Cadence Innovus:
```bash
innovus -stylus -f scripts/innovus_pnr.tcl
```

### Flow Highlights:
- **Floorplanning**: Core utilization of 65% with square aspect ratio (1.0). Pin placement on `Metal3` layers (North: `clock`, `resetb`; East: `MISO`; West: `SCK`, `CSB`, `MOSI`).
- **Power Distribution (PDN)**: Power rings on `Metal4` / `Metal5`, power stripes for vertical/horizontal grids, and follow-pin `sroute` on `Metal1`.
- **Placement**: Legalized cell placement with well-tap cells inserted every $30\mu\text{m}$ and row boundary endcap cells.
- **CTS**: Cadence CCOpt clock tree balancing with targeted skew $< 100\text{ ps}$.
- **Filler Insertion**: `FILL64` down to `FILL1` cells inserted prior to detail routing.
- **NanoRoute**: Grid-based detail routing with On-Chip Variation (OCV) analysis and Clock Path Pessimism Removal (CPPR).

---

## 5. Physical Signoff (Cadence PVS DRC & LVS)

Signoff verification using Cadence Physical Verification System (PVS):
```bash
# Execute Signoff DRC
csh scripts/run_pvs_drc.csh

# Execute Signoff LVS
csh scripts/run_pvs_lvs.csh
```
- **DRC Status**: Clean layout with **0 Design Rule Violations** (`spi_slave.sum`).
- **LVS Status**: **`LVS STATUS: CORRECT - LAYOUT AND SOURCE NETLIST ARE EQUIVALENT`** (`spi_slave.rep`).

---

## 🖼 Physical Layout & Verification Gallery

| Floorplan & Pin Allocation | Power Distribution Network |
|---|---|
| ![Floorplan](project_spi_images/IN%20floorplaning%20_%209.png) | ![Power Planning](project_spi_images/innvous%20Power%2010.png) |

| Final NanoRoute Placement & Routing | Genus Synthesis Area Report |
|---|---|
| ![Placement & Routing](project_spi_images/final%20placement%20routing%2011.png) | ![Genus Area](project_spi_images/genus%20area%206.png) |

| Cadence PVS Signoff DRC (Clean) | Cadence PVS Signoff LVS (Matched) |
|---|---|
| ![PVS DRC](project_spi_images/DRC%2012.png) | ![PVS LVS](project_spi_images/LVS_13.png) |

---

## ⚡ Quick Start Command Playbook

| Phase | EDA Tool | Command |
|---|---|---|
| **RTL Simulation** | Cadence Xcelium | `xrun -64bit -timescale 1ns/1ps -access +rwc src/spi_slave.v tb/spi_slave_tb.v` |
| **Logic Synthesis** | Cadence Genus | `genus -f scripts/genus_synth.tcl` |
| **Formal LEC** | Cadence Conformal | `lec -xl -nogui -do scripts/conformal_lec.tcl` |
| **Place & Route** | Cadence Innovus | `innovus -stylus -f scripts/innovus_pnr.tcl` |
| **PVS DRC** | Cadence PVS | `csh scripts/run_pvs_drc.csh` |
| **PVS LVS** | Cadence PVS | `csh scripts/run_pvs_lvs.csh` |

---

## 👤 Author & Acknowledgments

- **Author**: [Harshit Joshi](https://github.com/Harshitjoshi7)
- **Technology**: 45nm Generic Process Design Kit (GPDK045)
- **EDA Infrastructure**: Cadence Design Systems (Genus, Innovus, Xcelium, Conformal, PVS)
