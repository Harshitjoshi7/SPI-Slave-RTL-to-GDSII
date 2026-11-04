"""
Generate a full RTL-to-GDSII PDF guide for the AND gate design.
Uses reportlab for PDF generation.
Run: python generate_pdf.py
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Preformatted,
    Table, TableStyle, HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import Flowable
import math

# ─────────────────────────────────────────────────────────────────
# Custom Flowable: AND gate symbol drawn with canvas
# ─────────────────────────────────────────────────────────────────
class AndGateSymbol(Flowable):
    """Draws a clean 2-input AND gate circuit symbol."""
    def __init__(self, width=200, height=120):
        Flowable.__init__(self)
        self.width = width
        self.height = height

    def draw(self):
        c = self.canv
        c.saveState()

        # Center vertically
        oy = (self.height - 70) / 2
        ox = 30

        # AND gate body
        c.setStrokeColor(colors.HexColor('#1a237e'))
        c.setFillColor(colors.HexColor('#e8eaf6'))
        c.setLineWidth(2)

        # Draw AND gate shape: rectangle left + semicircle right
        p = c.beginPath()
        p.moveTo(ox, oy)
        p.lineTo(ox + 40, oy)
        # Semicircle on right side
        p.arcTo(ox + 20, oy, ox + 80, oy + 60, 0, -180)  # No — manual arc
        p.close()

        # Manual AND gate shape
        p2 = c.beginPath()
        p2.moveTo(ox, oy)
        p2.lineTo(ox, oy + 60)           # left vertical
        p2.lineTo(ox + 40, oy + 60)      # top horizontal
        # Right arc (semicircle): center at (ox+40, oy+30), radius 30
        p2.arcTo(ox + 10, oy, ox + 70, oy + 60, 270, 180)
        p2.lineTo(ox, oy)
        c.drawPath(p2, fill=1, stroke=1)

        # Input lines
        c.setStrokeColor(colors.HexColor('#1a237e'))
        c.setLineWidth(1.5)
        # Input A (top)
        c.line(ox - 30, oy + 45, ox, oy + 45)
        # Input B (bottom)
        c.line(ox - 30, oy + 15, ox, oy + 15)
        # Output Y
        c.line(ox + 70, oy + 30, ox + 100, oy + 30)

        # Labels
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(colors.HexColor('#1a237e'))
        c.drawString(ox - 50, oy + 42, "A")
        c.drawString(ox - 50, oy + 12, "B")
        c.drawString(ox + 105, oy + 27, "Y")

        # Gate label inside
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor('#283593'))
        c.drawString(ox + 15, oy + 27, "AND")

        # Truth table on right side
        tt_x = ox + 160
        tt_y = oy
        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(colors.black)
        c.drawString(tt_x, tt_y + 55, "A  B  |  Y")
        c.line(tt_x - 2, tt_y + 52, tt_x + 68, tt_y + 52)
        c.setFont("Courier", 9)
        rows = [("0  0  |  0", '#c62828'), ("0  1  |  0", '#c62828'),
                ("1  0  |  0", '#c62828'), ("1  1  |  1", '#2e7d32')]
        for i, (txt, col) in enumerate(rows):
            c.setFillColor(colors.HexColor(col))
            c.drawString(tt_x, tt_y + 38 - i*14, txt)

        c.restoreState()

    def wrap(self, availWidth, availHeight):
        return (self.width, self.height)


# ─────────────────────────────────────────────────────────────────
# Custom Flowable: Flow diagram box
# ─────────────────────────────────────────────────────────────────
class FlowStep(Flowable):
    """Single rounded box for the flow diagram."""
    def __init__(self, text, width=420, height=36, bg='#1565C0', fg='#ffffff'):
        Flowable.__init__(self)
        self.text = text
        self.width = width
        self.height = height
        self.bg = bg
        self.fg = fg

    def draw(self):
        c = self.canv
        c.saveState()
        c.setFillColor(colors.HexColor(self.bg))
        c.setStrokeColor(colors.HexColor('#0D47A1'))
        c.setLineWidth(1)
        c.roundRect(0, 0, self.width, self.height, 6, fill=1, stroke=1)
        c.setFillColor(colors.white if self.fg == 'white' else colors.HexColor(self.fg))
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(self.width / 2, self.height / 2 - 4, self.text)
        c.restoreState()

    def wrap(self, aw, ah):
        return (self.width, self.height)


class Arrow(Flowable):
    def __init__(self, width=420):
        Flowable.__init__(self)
        self.width = width
        self.height = 18

    def draw(self):
        c = self.canv
        c.saveState()
        cx = self.width / 2
        c.setStrokeColor(colors.HexColor('#1565C0'))
        c.setFillColor(colors.HexColor('#1565C0'))
        c.setLineWidth(1.5)
        c.line(cx, 18, cx, 6)
        # Arrowhead
        p = c.beginPath()
        p.moveTo(cx, 0)
        p.lineTo(cx - 5, 8)
        p.lineTo(cx + 5, 8)
        p.close()
        c.drawPath(p, fill=1, stroke=0)
        c.restoreState()

    def wrap(self, aw, ah):
        return (self.width, self.height)


# ─────────────────────────────────────────────────────────────────
# Styles
# ─────────────────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    title = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=colors.HexColor('#0D47A1'),
        spaceAfter=8,
        alignment=TA_CENTER,
        leading=32
    )
    subtitle = ParagraphStyle(
        'Subtitle',
        fontName='Helvetica',
        fontSize=13,
        textColor=colors.HexColor('#1565C0'),
        spaceAfter=6,
        alignment=TA_CENTER
    )
    chapter = ParagraphStyle(
        'Chapter',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=colors.white,
        backColor=colors.HexColor('#1565C0'),
        spaceBefore=16,
        spaceAfter=8,
        leftIndent=-6,
        rightIndent=-6,
        borderPad=6,
        leading=22
    )
    section = ParagraphStyle(
        'Section',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=colors.HexColor('#1565C0'),
        spaceBefore=12,
        spaceAfter=4,
        borderPad=2,
        leftIndent=0
    )
    body = ParagraphStyle(
        'BodyText2',
        fontName='Helvetica',
        fontSize=10,
        leading=16,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    note = ParagraphStyle(
        'Note',
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=colors.HexColor('#555555'),
        leftIndent=12,
        spaceAfter=4
    )
    bullet = ParagraphStyle(
        'Bullet2',
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        leftIndent=18,
        bulletIndent=6,
        spaceAfter=2
    )
    code_style = ParagraphStyle(
        'CodeStyle',
        fontName='Courier',
        fontSize=8.5,
        leading=13,
        textColor=colors.HexColor('#1a1a2e'),
        backColor=colors.HexColor('#f5f5f5'),
        leftIndent=8,
        rightIndent=8,
        spaceAfter=2,
        spaceBefore=2,
        borderColor=colors.HexColor('#bbdefb'),
        borderWidth=1,
        borderPad=6,
        borderRadius=4
    )
    label = ParagraphStyle(
        'Label',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.HexColor('#0D47A1'),
        backColor=colors.HexColor('#e3f2fd'),
        leftIndent=6,
        spaceAfter=0,
        spaceBefore=8,
        borderPad=3
    )
    return dict(
        title=title, subtitle=subtitle, chapter=chapter,
        section=section, body=body, note=note, bullet=bullet,
        code=code_style, label=label
    )


# ─────────────────────────────────────────────────────────────────
# Helper: code block
# ─────────────────────────────────────────────────────────────────
def code_block(text, styles, lang="", title=""):
    items = []
    if title:
        items.append(Paragraph(f"▶ {title}", styles['label']))
    items.append(Preformatted(text, styles['code']))
    return items


# ─────────────────────────────────────────────────────────────────
# Helper: section header
# ─────────────────────────────────────────────────────────────────
def section_h(text, styles):
    return [Spacer(1, 4*mm), Paragraph(text, styles['section'])]


def chapter_h(text, styles):
    return [PageBreak(), Paragraph(f"  {text}", styles['chapter']), Spacer(1, 4*mm)]


# ─────────────────────────────────────────────────────────────────
# Content builders
# ─────────────────────────────────────────────────────────────────

def cover_page(styles):
    elems = []
    elems.append(Spacer(1, 2*cm))
    elems.append(Paragraph("RTL to GDSII", styles['title']))
    elems.append(Paragraph("Complete ASIC Implementation Guide", styles['subtitle']))
    elems.append(Spacer(1, 4*mm))
    elems.append(Paragraph("Design Under Test: 2-Input AND Gate", styles['subtitle']))
    elems.append(Spacer(1, 6*mm))
    elems.append(HRFlowable(width="90%", thickness=2, color=colors.HexColor('#1565C0')))
    elems.append(Spacer(1, 6*mm))

    # AND gate symbol
    elems.append(AndGateSymbol(width=380, height=110))
    elems.append(Spacer(1, 6*mm))
    elems.append(HRFlowable(width="90%", thickness=1, color=colors.HexColor('#90caf9')))
    elems.append(Spacer(1, 6*mm))

    # Metadata table
    meta = [
        ["Technology Node", "45 nm GPDK (Generic PDK)"],
        ["EDA Tools", "Cadence Genus · Innovus · Conformal LEC · PVS"],
        ["Simulator", "Cadence Xcelium (xrun)"],
        ["Design Language", "Verilog-2001"],
        ["Target Frequency", "100 MHz (10 ns period, combinational)"],
        ["Output Deliverables", "Gate netlist · GDSII · SPEF · SDF · DRC/LVS reports"],
    ]
    t = Table(meta, colWidths=[5.5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1565C0')),
        ('TEXTCOLOR',  (0, 0), (0, -1), colors.white),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#e3f2fd')),
        ('ROWBACKGROUNDS', (1, 1), (1, -1), [colors.HexColor('#e3f2fd'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90caf9')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 1*cm))
    elems.append(Paragraph(
        "This guide walks through every phase of digital ASIC implementation—from "
        "writing synthesizable RTL Verilog, running functional simulation with Cadence "
        "Xcelium (xrun), logic synthesis with Genus, formal equivalence checking with "
        "Conformal LEC, full Place &amp; Route with Innovus, through physical "
        "verification (DRC &amp; LVS) with PVS and final GDSII tapeout.",
        styles['body']
    ))
    elems.append(PageBreak())
    return elems


def flow_diagram(styles):
    elems = []
    elems.append(Paragraph("  RTL-to-GDSII Implementation Flow", styles['chapter']))
    elems.append(Spacer(1, 4*mm))

    steps = [
        ("STEP 1 — RTL Design  (and_gate.v)",            '#1565C0'),
        ("STEP 2 — Testbench & xrun Simulation",          '#1565C0'),
        ("STEP 3 — SDC Timing Constraints",               '#283593'),
        ("STEP 4 — Logic Synthesis  (Cadence Genus)",     '#283593'),
        ("STEP 5 — Formal Verification  (Conformal LEC)", '#4527A0'),
        ("STEP 6 — MMMC Setup  (Slow/Fast Corners)",      '#283593'),
        ("STEP 7 — Floorplan & Initialization  (Innovus)","#1565C0"),
        ("STEP 8 — Power Planning  (Rings + Stripes)",    '#1565C0'),
        ("STEP 9 — Placement  (place_opt_design)",        '#1565C0'),
        ("STEP 10 — CTS  (ccopt_design -cts)",            '#283593'),
        ("STEP 11 — Routing  (routeDesign / NanoRoute)",  '#283593'),
        ("STEP 12 — RC Extraction & STA Signoff",         '#4527A0'),
        ("STEP 13 — DRC Signoff  (Cadence PVS)",          '#AD1457'),
        ("STEP 14 — LVS Signoff  (Cadence PVS)",          '#AD1457'),
        ("STEP 15 — GDSII Stream Out  ✔ Tapeout",         '#1B5E20'),
    ]
    for i, (label, color) in enumerate(steps):
        elems.append(FlowStep(label, width=430, height=30, bg=color))
        if i < len(steps) - 1:
            elems.append(Arrow(width=430))
    return elems


def rtl_section(styles):
    elems = chapter_h("STEP 1 — RTL Design: 2-Input AND Gate", styles)

    elems.append(Paragraph(
        "The AND gate is the fundamental combinational logic building block. "
        "Its output Y is HIGH only when <b>both</b> inputs A and B are HIGH. "
        "The synthesizable Verilog RTL below uses a single continuous assignment "
        "which Genus maps directly to an AND2 standard cell.",
        styles['body']
    ))

    # Truth table
    elems += section_h("Truth Table", styles)
    tt = Table(
        [["Input A", "Input B", "Output Y = A & B"],
         ["0", "0", "0"],
         ["0", "1", "0"],
         ["1", "0", "0"],
         ["1", "1", "1"]],
        colWidths=[4*cm, 4*cm, 6*cm]
    )
    tt.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',   (0, 1), (-1, -1), 'Courier'),
        ('FONTSIZE',   (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#ffebee'), colors.HexColor('#ffebee'),
          colors.HexColor('#ffebee'), colors.HexColor('#e8f5e9')]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#90caf9')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    elems.append(t := tt)
    elems.append(Spacer(1, 4*mm))

    elems += section_h("Verilog RTL Source  —  and_gate.v", styles)
    elems += code_block(
        "// File: src/and_gate.v\n"
        "// Module: and_gate\n"
        "// Desc  : 2-input AND gate — synthesizable Verilog-2001\n"
        "//\n"
        "// Port Map:\n"
        "//   a  — Input  A\n"
        "//   b  — Input  B\n"
        "//   y  — Output Y = A & B\n"
        "// ─────────────────────────────────────────────────────────────────\n"
        "\n"
        "module and_gate (\n"
        "    input  wire a,   // Input A\n"
        "    input  wire b,   // Input B\n"
        "    output wire y    // Output Y = A AND B\n"
        ");\n"
        "\n"
        "    // Continuous assignment — synthesizes to a single AND2 standard cell\n"
        "    assign y = a & b;\n"
        "\n"
        "endmodule",
        styles, title="src/and_gate.v"
    )

    elems += section_h("Key RTL Coding Guidelines", styles)
    for pt in [
        "<b>assign y = a & b;</b> — one-line combinational logic, no always block needed.",
        "Use <b>input wire</b> / <b>output wire</b> for combinational ports (no reg on output).",
        "No clock, no reset — pure combinational design has zero sequential elements.",
        "Bitwise <b>&amp;</b> operator synthesizes to an AND gate; logical <b>&amp;&amp;</b> is for conditions.",
        "The module compiles under <b>Verilog-2001</b> (ANSI port style).",
    ]:
        elems.append(Paragraph(f"• {pt}", styles['bullet']))
    return elems


def tb_section(styles):
    elems = chapter_h("STEP 2 — Testbench & Cadence Xcelium Simulation", styles)

    elems.append(Paragraph(
        "Functional simulation verifies that the RTL behaves correctly before synthesis. "
        "Cadence <b>Xcelium</b> is the industry-standard Verilog/SystemVerilog simulator "
        "invoked through the <b>xrun</b> front-end command. The testbench applies all "
        "four input combinations of a 2-input AND gate and self-checks the output.",
        styles['body']
    ))

    elems += section_h("Testbench Source  —  and_gate_tb.v", styles)
    elems += code_block(
        "`timescale 1ns/1ps\n"
        "\n"
        "module and_gate_tb;\n"
        "\n"
        "    // ── DUT signals ──────────────────────────────────────────────\n"
        "    reg  a, b;\n"
        "    wire y;\n"
        "\n"
        "    // ── DUT instantiation ────────────────────────────────────────\n"
        "    and_gate uut (.a(a), .b(b), .y(y));\n"
        "\n"
        "    // ── Check task ───────────────────────────────────────────────\n"
        "    integer pass_cnt = 0, fail_cnt = 0;\n"
        "\n"
        "    task check;\n"
        "        input exp;\n"
        "        input [63:0] label;\n"
        "        begin\n"
        "            #1;\n"
        "            if (y === exp) begin\n"
        "                pass_cnt = pass_cnt + 1;\n"
        "                $display(\"[PASS] %0s | a=%b b=%b y=%b\", label, a, b, y);\n"
        "            end else begin\n"
        "                fail_cnt = fail_cnt + 1;\n"
        "                $display(\"[FAIL] %0s | a=%b b=%b y=%b (exp %b)\",\n"
        "                          label, a, b, y, exp);\n"
        "            end\n"
        "        end\n"
        "    endtask\n"
        "\n"
        "    // ── Stimulus: all 4 truth table combinations ─────────────────\n"
        "    initial begin\n"
        "        $display(\"=== AND Gate Testbench ===\");\n"
        "\n"
        "        a=0; b=0; check(1'b0, \"0 AND 0\");   // Y must be 0\n"
        "        a=0; b=1; check(1'b0, \"0 AND 1\");   // Y must be 0\n"
        "        a=1; b=0; check(1'b0, \"1 AND 0\");   // Y must be 0\n"
        "        a=1; b=1; check(1'b1, \"1 AND 1\");   // Y must be 1\n"
        "\n"
        "        $display(\"Results: %0d PASSED, %0d FAILED\", pass_cnt, fail_cnt);\n"
        "        if (fail_cnt == 0) $display(\">>> ALL TESTS PASSED <<<\");\n"
        "        $finish;\n"
        "    end\n"
        "\n"
        "endmodule",
        styles, title="tb/and_gate_tb.v"
    )

    elems += section_h("Cadence Xcelium (xrun) Commands", styles)

    cmds = [
        ("RTL Simulation", "xrun src/and_gate.v tb/and_gate_tb.v \\\n    -timescale 1ns/1ps \\\n    -access +rwc \\\n    -log sim_rtl.log"),
        ("RTL Sim + Waveform (SHM)", "xrun src/and_gate.v tb/and_gate_tb.v \\\n    -timescale 1ns/1ps \\\n    -access +rwc \\\n    -define DUMP_SHM \\\n    -shm \\\n    -log sim_rtl_waves.log"),
        ("Gate-Level Sim (post-synthesis)", "xrun netlist/and_gate_synth.v \\\n    $GPDK045/verilog/fast_vdd1v0_basicCells.v \\\n    tb/and_gate_tb.v \\\n    -timescale 1ns/1ps \\\n    -access +rwc \\\n    -delay_mode zero \\\n    +notimingcheck \\\n    -log sim_gate.log"),
        ("Post-Route Sim with SDF backannotation", "xrun netlist/and_gate_postroute.v \\\n    $GPDK045/verilog/fast_vdd1v0_basicCells.v \\\n    tb/and_gate_tb.v \\\n    -timescale 1ns/1ps \\\n    -access +rwc \\\n    -sdf_cmd_file scripts/sdf_annotate.cmd \\\n    -log sim_postroute.log"),
        ("Batch file approach (xrun -f)", "xrun -f scripts/sim_rtl.f"),
    ]
    for title_c, cmd in cmds:
        elems.append(Paragraph(f"▸ {title_c}", styles['label']))
        elems += code_block(cmd, styles)
        elems.append(Spacer(1, 2*mm))

    elems += section_h("Simulation File List  —  scripts/sim_rtl.f", styles)
    elems += code_block(
        "// Cadence xrun file-list for AND gate RTL simulation\n"
        "// Usage: xrun -f scripts/sim_rtl.f\n"
        "\n"
        "src/and_gate.v          // RTL source\n"
        "tb/and_gate_tb.v        // Self-checking testbench\n"
        "\n"
        "-timescale 1ns/1ps\n"
        "-access +rwc\n"
        "-64bit\n"
        "-clean\n"
        "-log sim_rtl.log\n"
        "-run",
        styles, title="scripts/sim_rtl.f"
    )

    elems += section_h("Expected xrun Console Output", styles)
    elems += code_block(
        "xrun: 20.09-s005\n"
        "Loading  src/and_gate.v\n"
        "Loading  tb/and_gate_tb.v\n"
        "Elaborating...\n"
        "\n"
        "=== AND Gate Testbench ===\n"
        "[PASS] 0 AND 0 | a=0 b=0 y=0\n"
        "[PASS] 0 AND 1 | a=0 b=1 y=0\n"
        "[PASS] 1 AND 0 | a=1 b=0 y=0\n"
        "[PASS] 1 AND 1 | a=1 b=1 y=1\n"
        "Results: 4 PASSED, 0 FAILED\n"
        ">>> ALL TESTS PASSED <<<\n"
        "\n"
        "Simulation complete.",
        styles, title="Expected Console Output"
    )
    return elems


def sdc_section(styles):
    elems = chapter_h("STEP 3 — SDC Timing Constraints", styles)
    elems.append(Paragraph(
        "The Synopsys Design Constraints (SDC) file provides the timing specification "
        "used by both Genus (synthesis) and Innovus (PnR). Since the AND gate is purely "
        "combinational, a virtual clock is defined as a timing reference for I/O budgets.",
        styles['body']
    ))
    elems += code_block(
        "###############################################################\n"
        "# File: constraints/and_gate.sdc\n"
        "# Design: and_gate (combinational)\n"
        "# Tool:   Cadence Genus / Innovus\n"
        "###############################################################\n"
        "\n"
        "# Virtual clock — 100 MHz reference for I/O timing budget\n"
        "create_clock -name vclk -period 10.0\n"
        "\n"
        "# Input arrival times (max = setup, min = hold budget)\n"
        "set_input_delay  -max 2.0 -clock vclk [get_ports {a b}]\n"
        "set_input_delay  -min 0.5 -clock vclk [get_ports {a b}]\n"
        "\n"
        "# Output required times\n"
        "set_output_delay -max 2.0 -clock vclk [get_ports y]\n"
        "set_output_delay -min 0.5 -clock vclk [get_ports y]\n"
        "\n"
        "# Drive strength of input ports (driven by INVX1 strength driver)\n"
        "set_driving_cell -lib_cell INVX1 [get_ports {a b}]\n"
        "\n"
        "# Capacitive load on output port (20 fF)\n"
        "set_load -pin_load 0.020 [get_ports y]",
        styles, title="constraints/and_gate.sdc"
    )
    return elems


def synthesis_section(styles):
    elems = chapter_h("STEP 4 — Logic Synthesis with Cadence Genus", styles)

    elems.append(Paragraph(
        "Cadence <b>Genus</b> translates the synthesizable Verilog RTL into a "
        "technology-specific gate-level netlist using the GPDK045 standard cell library. "
        "Synthesis is performed in three sequential stages: Generic → Technology Map → Optimization.",
        styles['body']
    ))

    elems += section_h("Run Command", styles)
    elems += code_block("genus -f scripts/genus_synth.tcl", styles)

    elems += section_h("Full Synthesis Script  —  scripts/genus_synth.tcl", styles)
    elems += code_block(
        "###############################################################\n"
        "# Cadence Genus Synthesis Script: and_gate\n"
        "# Usage: genus -f scripts/genus_synth.tcl\n"
        "###############################################################\n"
        "\n"
        "# ── 0. Create output directories ─────────────────────────────\n"
        "file mkdir reports\n"
        "file mkdir netlist\n"
        "\n"
        "# ── 1. Library search paths ──────────────────────────────────\n"
        "set GPDK /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs\n"
        "set LIB  /home/ec/install/FOUNDRY/digital/45nm/dig/lib\n"
        "\n"
        "set_db / .init_lib_search_path [list \\\n"
        "    $LIB \\\n"
        "    $GPDK/GPDK045/gsclib045_svt_v4.4/gsclib045/timing ]\n"
        "\n"
        "set_db / .init_hdl_search_path {./src}\n"
        "\n"
        "# ── 2. Target technology library (.lib) ───────────────────────\n"
        "set_db / .library { $LIB/typical.lib }\n"
        "\n"
        "# ── 3. Physical LEF (for area/wireload estimation) ────────────\n"
        "set_db / .lef_library [list \\\n"
        "    $GPDK/GPDK045/gsclib045_svt_v4.4/gsclib045_tech/lef/gsclib045_tech.lef \\\n"
        "    $GPDK/GPDK045/gsclib045_svt_v4.4/gsclib045/lef/gsclib045_macro.lef ]\n"
        "\n"
        "# ── 4. Read HDL & elaborate ───────────────────────────────────\n"
        "read_hdl -verilog src/and_gate.v\n"
        "elaborate and_gate\n"
        "\n"
        "check_design -unresolved\n"
        "\n"
        "# ── 5. Read timing constraints ────────────────────────────────\n"
        "read_sdc constraints/and_gate.sdc\n"
        "report_clocks > reports/clocks_synth.rpt\n"
        "\n"
        "# ── 6. Three-stage synthesis ──────────────────────────────────\n"
        "# Stage A: RTL → GTECH (technology-independent logic)\n"
        "syn_generic\n"
        "report_timing > reports/timing_generic.rpt\n"
        "\n"
        "# Stage B: GTECH → 45 nm standard cell gates\n"
        "syn_map\n"
        "report_timing > reports/timing_mapped.rpt\n"
        "\n"
        "# Stage C: Timing/area/power optimization\n"
        "syn_opt\n"
        "\n"
        "# ── 7. QoR reports ───────────────────────────────────────────\n"
        "check_design -all         > reports/check_design.rpt\n"
        "report_timing -nworst 10  > reports/timing_synth.rpt\n"
        "report_area               > reports/area_synth.rpt\n"
        "report_power              > reports/power_synth.rpt\n"
        "report_gates              > reports/gates_synth.rpt\n"
        "report_qor                > reports/qor_synth.rpt\n"
        "\n"
        "# ── 8. Export gate-level netlist & SDC ───────────────────────\n"
        "write_hdl  > netlist/and_gate_synth.v\n"
        "write_sdc  > netlist/and_gate_synth.sdc\n"
        "\n"
        "puts \"=== Genus Synthesis Complete ===\"",
        styles, title="scripts/genus_synth.tcl"
    )

    elems += section_h("Key Genus Commands Reference", styles)
    cmd_table = [
        ["Command", "Description"],
        ["genus -f <script>",       "Launch Genus and execute the Tcl script"],
        ["set_db / .library {...}",  "Set target .lib technology library"],
        ["set_db / .lef_library {}", "Set physical LEF files for geometry info"],
        ["read_hdl -verilog <file>", "Read Verilog RTL source file"],
        ["elaborate <top>",          "Compile, resolve hierarchy, check design"],
        ["check_design -unresolved", "Flag any blackbox / unresolved references"],
        ["read_sdc <file>",          "Import timing constraints (SDC format)"],
        ["syn_generic",              "Stage A: RTL to GTECH (tech-independent)"],
        ["syn_map",                  "Stage B: Map GTECH to target cell library"],
        ["syn_opt",                  "Stage C: Timing/area/power optimization"],
        ["report_timing -nworst N",  "Show N worst setup timing paths"],
        ["report_area",              "Report cell count, area, density"],
        ["report_power",             "Report dynamic + static power"],
        ["write_hdl",                "Export gate-level netlist (Verilog)"],
        ["write_sdc",                "Export synthesized timing constraints"],
    ]
    t = Table(cmd_table, colWidths=[5.5*cm, 10*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',   (0, 1), (-1, -1), 'Courier'),
        ('FONTNAME',   (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#e3f2fd'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#90caf9')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elems.append(t)

    elems += section_h("Expected Synthesized Gate Netlist  —  netlist/and_gate_synth.v", styles)
    elems += code_block(
        "// Genus auto-generated gate-level netlist\n"
        "// Technology: 45nm GPDK (SVT)\n"
        "\n"
        "module and_gate ( a, b, y );\n"
        "    input  a, b;\n"
        "    output y;\n"
        "\n"
        "    // Genus maps 'assign y = a & b' to a single AND2X1 standard cell\n"
        "    AND2X1 U_AND ( .A(a), .B(b), .Y(y) );\n"
        "\n"
        "endmodule",
        styles, title="netlist/and_gate_synth.v  (Genus output)"
    )
    return elems


def lec_section(styles):
    elems = chapter_h("STEP 5 — Formal Verification with Conformal LEC", styles)

    elems.append(Paragraph(
        "Cadence <b>Conformal LEC</b> formally proves (mathematically, without simulation) "
        "that the synthesized gate-level netlist is <i>logically equivalent</i> to the "
        "original RTL. For a simple AND gate this is trivially provable but the same "
        "methodology scales to million-gate designs.",
        styles['body']
    ))

    elems += section_h("Run Command", styles)
    elems += code_block("lec -xl -nogui -do scripts/conformal_lec.tcl", styles)

    elems += section_h("LEC Script  —  scripts/conformal_lec.tcl", styles)
    elems += code_block(
        "###############################################################\n"
        "# Cadence Conformal LEC: RTL vs. Gate Netlist\n"
        "# Usage: lec -xl -nogui -do scripts/conformal_lec.tcl\n"
        "###############################################################\n"
        "\n"
        "set_log_file lec_results.log -replace\n"
        "\n"
        "# Flattening options\n"
        "set_flatten_model -seq_constant -all\n"
        "set_flatten_model -nodeset_to_constraint\n"
        "\n"
        "# ── 1. Golden design = RTL ────────────────────────────────────\n"
        "read_library -liberty /home/ec/install/FOUNDRY/digital/45nm/dig/lib/typical.lib -both\n"
        "read_design src/and_gate.v -verilog -golden -lastmod\n"
        "set_root_module and_gate -golden\n"
        "\n"
        "# ── 2. Revised design = synthesized gate netlist ──────────────\n"
        "read_design netlist/and_gate_synth.v -verilog -revised -lastmod\n"
        "set_root_module and_gate -revised\n"
        "\n"
        "# ── 3. Map compare points ────────────────────────────────────\n"
        "set_system_mode lec\n"
        "map_key_points\n"
        "report_unmapped_points\n"
        "\n"
        "# ── 4. Run formal comparison ─────────────────────────────────\n"
        "add_compare_points -all\n"
        "compare\n"
        "\n"
        "# ── 5. Report results ─────────────────────────────────────────\n"
        "report_compare_data -nonequivalent\n"
        "puts \"=== LEC: Formal proof complete ===\"",
        styles, title="scripts/conformal_lec.tcl"
    )

    elems += section_h("Expected LEC Output (PASS)", styles)
    elems += code_block(
        "Reading library: typical.lib\n"
        "Reading golden  : src/and_gate.v\n"
        "Reading revised : netlist/and_gate_synth.v\n"
        "\n"
        "Mapping key points...\n"
        "Mapped output  :  y  <-->  y\n"
        "\n"
        "Running formal comparison...\n"
        "\n"
        "Compared points  :  1\n"
        "Equivalent       :  1\n"
        "Non-equivalent   :  0\n"
        "Abort            :  0\n"
        "\n"
        ">>> FORMAL VERIFICATION PASSED <<<",
        styles, title="Expected Console Output"
    )
    return elems


def mmmc_section(styles):
    elems = chapter_h("STEP 6 — Multi-Mode Multi-Corner (MMMC) Setup", styles)
    elems.append(Paragraph(
        "MMMC analysis runs setup and hold checks simultaneously across the worst-case "
        "(Slow, 125°C) and best-case (Fast, 0°C) process-voltage-temperature corners.",
        styles['body']
    ))
    elems += code_block(
        "###############################################################\n"
        "# File: scripts/mmmc.tcl — Cadence Innovus MMMC configuration\n"
        "###############################################################\n"
        "\n"
        "set GPDK /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs\n"
        "set TIM  $GPDK/GPDK045/gsclib045_svt_v4.4/gsclib045/timing\n"
        "\n"
        "# Slow corner: Worst-case setup (slow process, 125°C, low VDD)\n"
        "create_library_set -name slow_libs -timing [\n"
        "    list $TIM/slow_vdd1v0_basicCells.lib \\\n"
        "         $TIM/slow_vdd1v0_multibitsDFF.lib]\n"
        "\n"
        "# Fast corner: Best-case hold (fast process, 0°C, high VDD)\n"
        "create_library_set -name fast_libs -timing [\n"
        "    list $TIM/fast_vdd1v0_basicCells.lib \\\n"
        "         $TIM/fast_vdd1v0_multibitsDFF.lib]\n"
        "\n"
        "# RC corners (interconnect resistance/capacitance model)\n"
        "create_rc_corner -name slow_rc -temperature 125\n"
        "create_rc_corner -name fast_rc -temperature 0\n"
        "\n"
        "# Delay corners (cell timing + interconnect RC)\n"
        "create_delay_corner -name slow_delay \\\n"
        "    -library_set slow_libs -rc_corner slow_rc\n"
        "create_delay_corner -name fast_delay \\\n"
        "    -library_set fast_libs -rc_corner fast_rc\n"
        "\n"
        "# Constraint mode (SDC exported from Genus)\n"
        "create_constraint_mode -name func_mode \\\n"
        "    -sdc_files {netlist/and_gate_synth.sdc}\n"
        "\n"
        "# Analysis views\n"
        "create_analysis_view -name slow_view \\\n"
        "    -constraint_mode func_mode -delay_corner slow_delay\n"
        "create_analysis_view -name fast_view \\\n"
        "    -constraint_mode func_mode -delay_corner fast_delay\n"
        "\n"
        "# Assign views: Setup = slow, Hold = fast\n"
        "set_analysis_view -setup {slow_view} -hold {fast_view}",
        styles, title="scripts/mmmc.tcl"
    )
    return elems


def innovus_section(styles):
    elems = chapter_h("STEP 7–11 — Place & Route with Cadence Innovus", styles)

    elems.append(Paragraph(
        "Cadence <b>Innovus</b> takes the gate-level netlist and physically places standard "
        "cells on a silicon die, connects power networks, synthesizes the clock tree (for "
        "sequential designs), routes all signal wires, and verifies the physical design "
        "before producing the final GDSII layout.",
        styles['body']
    ))

    elems += section_h("Master Run Command", styles)
    elems += code_block(
        "# Run complete PnR flow in batch\n"
        "innovus -stylus -f scripts/innovus_pnr.tcl\n"
        "\n"
        "# OR: Launch interactive GUI, then source scripts step by step\n"
        "innovus\n"
        "  > source scripts/step1_init.tcl\n"
        "  > source scripts/step2_floorplan.tcl\n"
        "  > source scripts/step3_power.tcl\n"
        "  > source scripts/step4_place.tcl\n"
        "  > source scripts/step5_cts.tcl\n"
        "  > source scripts/step6_route.tcl\n"
        "  > source scripts/step7_export.tcl",
        styles, title="Innovus Invocation"
    )

    steps_data = [
        ("Step 1: Initialization", "scripts/step1_init.tcl",
         "catch {freeDesign}\n"
         "\n"
         "# Read MMMC configuration\n"
         "read_mmmc scripts/mmmc.tcl\n"
         "\n"
         "# Read physical LEF files\n"
         "read_physical -lefs {\n"
         "    $GPDK/gsclib045_tech/lef/gsclib045_tech.lef\n"
         "    $GPDK/gsclib045/lef/gsclib045_macro.lef\n"
         "}\n"
         "\n"
         "# Read synthesized gate netlist\n"
         "read_netlist netlist/and_gate_synth.v -top and_gate\n"
         "\n"
         "# Initialize the design database\n"
         "init_design\n"
         "puts \"=== Step 1: Init complete ===\""),

        ("Step 2: Floorplan & Pin Placement", "scripts/step2_floorplan.tcl",
         "# Core: Aspect ratio 1.0 (square), utilization 65%\n"
         "# Margins: Left=10um Bottom=10um Right=10um Top=10um\n"
         "floorPlan -r 1.0 0.65 10 10 10 10\n"
         "\n"
         "# Place ports on Metal3 on appropriate sides\n"
         "editPin -side West -pin {a b} -layer Metal3\n"
         "editPin -side East -pin {y}   -layer Metal3\n"
         "\n"
         "puts \"=== Step 2: Floorplan complete ===\""),

        ("Step 3: Power Planning (PDN)", "scripts/step3_power.tcl",
         "# Connect power/ground nets to all cell pins\n"
         "globalNetConnect VDD -type pgpin -pin VDD -inst * -all\n"
         "globalNetConnect VSS -type pgpin -pin VSS -inst * -all\n"
         "\n"
         "# Core power rings (Metal4 horizontal, Metal5 vertical)\n"
         "addRing -type core_rings -nets {VDD VSS} \\\n"
         "    -layer {top Metal5 bottom Metal5 left Metal4 right Metal4} \\\n"
         "    -width 1.5 -spacing 0.5 -offset 2.0\n"
         "\n"
         "# Vertical VDD/VSS stripes on Metal5\n"
         "addStripe -nets {VDD VSS} -layer Metal5 -direction vertical \\\n"
         "    -width 1.0 -spacing 0.5 -set_to_set_distance 40\n"
         "\n"
         "# Connect standard cell rails (Metal1 follow-pins)\n"
         "sroute -connect {blockPin padPin corePin} \\\n"
         "    -layerChangeRange {Metal1 Metal5} \\\n"
         "    -nets {VDD VSS}\n"
         "\n"
         "puts \"=== Step 3: Power planning complete ===\""),

        ("Step 4: Placement", "scripts/step4_place.tcl",
         "# Insert boundary end-cap cells\n"
         "catch {addEndCap -prefix ENDCAP}\n"
         "\n"
         "# Insert well-tap cells to prevent latch-up (every 30 um)\n"
         "catch {addWellTap -cell WELLTAP -cellInterval 30 -prefix WELLTAP}\n"
         "\n"
         "# Timing-driven standard cell placement\n"
         "place_opt_design\n"
         "\n"
         "# Verify placement legality (no overlaps)\n"
         "checkPlace\n"
         "\n"
         "# Pre-CTS timing report (ideal clocks)\n"
         "timeDesign -preCTS -outDir reports/preCTS\n"
         "\n"
         "puts \"=== Step 4: Placement complete ===\""),

        ("Step 5: CTS (Clock Tree Synthesis)", "scripts/step5_cts.tcl",
         "# Note: AND gate is combinational (no clock).\n"
         "# CTS step is included here for completeness and\n"
         "# is required in sequential designs.\n"
         "\n"
         "# For combinational-only: run a timing check\n"
         "timeDesign -preCTS -outDir reports/preCTS\n"
         "\n"
         "# ─── For sequential designs: ─────────────────────────────────\n"
         "# set_ccopt_property buffer_cells {CLKBUFX2 CLKBUFX4 BUFX4}\n"
         "# set_ccopt_property inverter_cells {INVX1 INVX2 CLKINVX1}\n"
         "# set_ccopt_property target_skew 0.1\n"
         "# set_ccopt_property target_max_trans 0.3\n"
         "# create_ccopt_clock_tree_spec -file ccopt.spec\n"
         "# source ccopt.spec\n"
         "# ccopt_design -cts\n"
         "# timeDesign -postCTS -outDir reports/postCTS\n"
         "# optDesign  -postCTS\n"
         "# optDesign  -postCTS -hold\n"
         "\n"
         "puts \"=== Step 5: CTS complete ===\""),

        ("Step 6: Filler Insertion & Routing", "scripts/step6_route.tcl",
         "# Insert filler cells to fill all standard-cell row gaps\n"
         "catch {addFiller -cell {FILL64 FILL32 FILL16 FILL8 FILL4 FILL2 FILL1} \\\n"
         "                 -prefix FILLER}\n"
         "\n"
         "# Verify no gaps remain\n"
         "checkPlace\n"
         "\n"
         "# Run NanoRoute detail routing\n"
         "routeDesign\n"
         "\n"
         "# Enable OCV analysis with CPPR\n"
         "setAnalysisMode -analysisType onChipVariation -cppr both\n"
         "\n"
         "# Post-route timing optimization (setup + hold)\n"
         "optDesign -postRoute\n"
         "optDesign -postRoute -hold\n"
         "\n"
         "# Post-route timing verification\n"
         "timeDesign -postRoute      -outDir reports/postRoute\n"
         "timeDesign -postRoute -hold -outDir reports/postRoute_hold\n"
         "\n"
         "puts \"=== Step 6: Routing complete ===\""),
    ]

    for step_name, filename, code in steps_data:
        elems += section_h(step_name, styles)
        elems += code_block(code, styles, title=filename)
        elems.append(Spacer(1, 2*mm))

    return elems


def rc_signoff_section(styles):
    elems = chapter_h("STEP 12 — RC Extraction & Timing Signoff", styles)
    elems.append(Paragraph(
        "After routing, parasitics (resistance R and capacitance C) of all metal interconnects "
        "are extracted into <b>SPEF</b> format and back-annotated into the static timing "
        "analysis engine for accurate signoff-quality timing verification.",
        styles['body']
    ))
    elems += code_block(
        "###############################################################\n"
        "# File: scripts/step7_export.tcl\n"
        "# Step 7: Physical Verification, RC Extraction, GDSII Export\n"
        "###############################################################\n"
        "\n"
        "# ── Quick DRC & connectivity check (inside Innovus) ──────────\n"
        "verify_drc\n"
        "verifyConnectivity -type all -error 1000 -warning 50\n"
        "catch {verifyProcessAntenna}\n"
        "\n"
        "# ── Export post-route netlists ────────────────────────────────\n"
        "# Logical netlist (for LEC and gate-level simulation)\n"
        "saveNetlist netlist/and_gate_postroute.v\n"
        "\n"
        "# With power/ground pins (required for PVS LVS)\n"
        "saveNetlist -includePowerGround netlist/and_gate_postroute_pg.v\n"
        "\n"
        "# ── Parasitic extraction ──────────────────────────────────────\n"
        "setExtractRCMode -engine postRoute -effortLevel signoff\n"
        "extractRC\n"
        "rcOut -spef netlist/and_gate_postroute.spef\n"
        "\n"
        "# ── SDF for post-route gate-level simulation ──────────────────\n"
        "write_sdf -version 3.0 netlist/and_gate_postroute.sdf\n"
        "\n"
        "# ── Final signoff static timing analysis ─────────────────────\n"
        "timeDesign -signoff      -outDir reports/signoff\n"
        "timeDesign -signoff -hold -outDir reports/signoff_hold\n"
        "\n"
        "# ── GDSII stream out ──────────────────────────────────────────\n"
        "streamOut output/and_gate.gds \\\n"
        "    -mapFile   $GPDK/gsclib045_tech/gds/gds2.map \\\n"
        "    -merge     $GPDK/gsclib045/gds/gsclib045.gds \\\n"
        "    -libName   and_gate \\\n"
        "    -structureName and_gate \\\n"
        "    -units 2000 \\\n"
        "    -mode ALL\n"
        "\n"
        "# ── Save Innovus session database ─────────────────────────────\n"
        "saveDesign output/and_gate_final.enc\n"
        "\n"
        "puts \"=== PnR + Export Complete ===\"",
        styles, title="scripts/step7_export.tcl"
    )

    elems += section_h("Key Innovus Signoff Commands Reference", styles)
    cmd_tbl = [
        ["Command", "Description"],
        ["verify_drc",                    "Internal DRC check (quick, pre-PVS)"],
        ["verifyConnectivity -type all",  "Check power/ground/signal connectivity"],
        ["verifyProcessAntenna",          "Check metal antenna rule violations"],
        ["saveNetlist <file>",            "Export logical post-route netlist"],
        ["saveNetlist -includePowerGround","Export netlist with VDD/VSS pins (LVS)"],
        ["setExtractRCMode -engine postRoute", "Configure RC extractor engine"],
        ["extractRC",                     "Run parasitic RC extraction"],
        ["rcOut -spef <file>",            "Write SPEF file (parasitics)"],
        ["write_sdf -version 3.0 <file>", "Write SDF timing annotation file"],
        ["timeDesign -signoff",           "Final STA with extracted parasitics"],
        ["streamOut <gds> -mapFile ...",  "Stream GDSII output with layer map"],
        ["saveDesign <file>",             "Save Innovus database for re-entry"],
    ]
    t = Table(cmd_tbl, colWidths=[6*cm, 9.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1565C0')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',   (0, 1), (-1, -1), 'Courier'),
        ('FONTNAME',   (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#e3f2fd'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#90caf9')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elems.append(t)
    return elems


def pvs_section(styles):
    elems = chapter_h("STEP 13–14 — Physical Verification: DRC & LVS (Cadence PVS)", styles)
    elems.append(Paragraph(
        "Cadence <b>PVS</b> (Physical Verification System) is the signoff physical "
        "verification tool. <b>DRC</b> checks that the GDSII layout conforms to all "
        "foundry manufacturing rules. <b>LVS</b> proves that the layout connectivity "
        "exactly matches the logical gate netlist.",
        styles['body']
    ))

    elems += section_h("DRC — Design Rule Check", styles)
    elems += code_block(
        "#!/bin/csh -f\n"
        "# File: scripts/run_pvs_drc.csh\n"
        "# Cadence PVS DRC Signoff — and_gate\n"
        "\n"
        "mkdir -p pvs_output/drc\n"
        "\n"
        "pvs -drc \\\n"
        "    -gds      output/and_gate.gds \\\n"
        "    -top_cell and_gate \\\n"
        "    -run_dir  pvs_output/drc \\\n"
        "    /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlDRC.rul\n"
        "\n"
        "echo \"DRC Report: pvs_output/drc/and_gate.sum\"",
        styles, title="scripts/run_pvs_drc.csh"
    )
    elems.append(Paragraph(
        "✔ Signoff requires: <b>Total DRC Violations: 0</b> in <code>pvs_output/drc/and_gate.sum</code>",
        styles['note']
    ))

    elems += section_h("LVS — Layout Versus Schematic", styles)
    elems += code_block(
        "#!/bin/csh -f\n"
        "# File: scripts/run_pvs_lvs.csh\n"
        "# Cadence PVS LVS Signoff — and_gate\n"
        "\n"
        "mkdir -p pvs_output/lvs\n"
        "\n"
        "set GPDK = /home/ec/install/FOUNDRY/lan/flow/t1u1/reference_libs\n"
        "\n"
        "pvs -lvs \\\n"
        "    -automatch \\\n"
        "    -hcell            scripts/hcells.txt \\\n"
        "    -gds              output/and_gate.gds \\\n"
        "    -top_cell         and_gate \\\n"
        "    -source_top_cell  and_gate \\\n"
        "    -source_verilog   netlist/and_gate_postroute_pg.v \\\n"
        "    -source_cdl $GPDK/GPDK045/gsclib045_svt_v4.4/gsclib045/cdl/gsclib045.cdl \\\n"
        "    -control          scripts/pvs_lvs.ctrl \\\n"
        "    -run_dir          pvs_output/lvs \\\n"
        "    /home/ec/install/FOUNDRY/analog/45nm/pvs/pvlLVS.rul\n"
        "\n"
        "echo \"LVS Report: pvs_output/lvs/and_gate.rep\"",
        styles, title="scripts/run_pvs_lvs.csh"
    )
    elems.append(Paragraph(
        "✔ Signoff requires: <b>LVS STATUS: CORRECT — LAYOUT AND SOURCE NETLIST ARE EQUIVALENT</b>",
        styles['note']
    ))

    return elems


def gds_section(styles):
    elems = chapter_h("STEP 15 — GDSII Stream Out & Tapeout", styles)
    elems.append(Paragraph(
        "The final step streams the physical layout to <b>GDSII</b> (Graphic Design System II) "
        "format — the standard mask-data format delivered to the silicon foundry for "
        "photomask fabrication. The <b>layer map file</b> translates Innovus internal layer "
        "names (Metal1, Metal2…) to GDS layer/datatype numbers required by the PDK.",
        styles['body']
    ))

    elems += section_h("Output Deliverables Summary", styles)
    deliverables = [
        ["File", "Path", "Purpose"],
        ["Gate Netlist",      "netlist/and_gate_synth.v",        "Synthesis output (Genus)"],
        ["Synthesized SDC",   "netlist/and_gate_synth.sdc",      "Timing constraints for PnR"],
        ["Post-Route Netlist","netlist/and_gate_postroute.v",    "For LEC and gate-sim"],
        ["PG Netlist",        "netlist/and_gate_postroute_pg.v", "For PVS LVS (has VDD/VSS)"],
        ["SPEF",              "netlist/and_gate_postroute.spef", "Parasitic RC extraction"],
        ["SDF",               "netlist/and_gate_postroute.sdf",  "Timing annotation for sim"],
        ["GDSII",             "output/and_gate.gds",            "Final tapeout mask data"],
        ["Innovus DB",        "output/and_gate_final.enc",       "Re-entry / ECO database"],
        ["DRC Report",        "pvs_output/drc/and_gate.sum",    "DRC signoff results"],
        ["LVS Report",        "pvs_output/lvs/and_gate.rep",    "LVS signoff results"],
    ]
    t = Table(deliverables, colWidths=[4*cm, 6.5*cm, 5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1B5E20')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',   (0, 1), (-1, -1), 'Courier'),
        ('FONTNAME',   (1, 1), (-1, -1), 'Courier'),
        ('FONTNAME',   (2, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#e8f5e9'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#a5d6a7')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elems.append(t)
    return elems


def cheatsheet_section(styles):
    elems = chapter_h("Master Command Cheat Sheet", styles)

    all_cmds = [
        ["Phase", "Tool", "Command"],
        ["RTL Simulation",        "Cadence Xcelium",  "xrun -f scripts/sim_rtl.f"],
        ["Gate-Level Sim",        "Cadence Xcelium",  "xrun -f scripts/gate_sim.f"],
        ["Post-Route Sim",        "Cadence Xcelium",  "xrun -f scripts/postroute_sim.f"],
        ["Logic Synthesis",       "Cadence Genus",    "genus -f scripts/genus_synth.tcl"],
        ["Formal Verification",   "Conformal LEC",    "lec -xl -nogui -do scripts/conformal_lec.tcl"],
        ["Place & Route (batch)", "Cadence Innovus",  "innovus -stylus -f scripts/innovus_pnr.tcl"],
        ["Interactive PnR",       "Cadence Innovus",  "innovus"],
        ["DRC Signoff",           "Cadence PVS",      "csh scripts/run_pvs_drc.csh"],
        ["LVS Signoff",           "Cadence PVS",      "csh scripts/run_pvs_lvs.csh"],
    ]
    t = Table(all_cmds, colWidths=[4*cm, 4.5*cm, 7*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0D47A1')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',   (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME',   (1, 1), (1, -1), 'Helvetica'),
        ('FONTNAME',   (2, 1), (2, -1), 'Courier'),
        ('TEXTCOLOR',  (0, 1), (0, -1), colors.HexColor('#0D47A1')),
        ('FONTSIZE',   (0, 0), (-1, -1), 8.5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#e3f2fd'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#90caf9')),
        ('PADDING', (0, 0), (-1, -1), 5),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elems.append(t)

    elems += section_h("Common Debug Quick-Fixes", styles)
    debug_tbl = [
        ["Issue", "Symptom", "Fix"],
        ["Negative setup slack", "timeDesign shows WNS < 0",
         "optDesign -postRoute -setup\nsetOptMode -effort high"],
        ["Hold violations", "WHS < 0 after routing",
         "deleteFiller → optDesign -postRoute -hold\n→ ecoRoute → addFiller"],
        ["DRC errors", "pvs_output/drc/*.sum non-zero",
         "Check antenna, min-width, spacing;\nrerun routeDesign -fixDRC"],
        ["LVS mismatch", "PG netlist mismatch",
         "Use saveNetlist -includePowerGround;\ncheck hcells.txt CDL mapping"],
        ["Elaboration fail", "check_design: unresolved refs",
         "Check .init_hdl_search_path;\nconfirm module name matches file name"],
    ]
    t2 = Table(debug_tbl, colWidths=[3.5*cm, 4.5*cm, 7.5*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#B71C1C')),
        ('TEXTCOLOR',  (0, 0), (-1, 0), colors.white),
        ('FONTNAME',   (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME',   (0, 1), (1, -1), 'Helvetica'),
        ('FONTNAME',   (2, 1), (2, -1), 'Courier'),
        ('FONTSIZE',   (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1),
         [colors.HexColor('#ffebee'), colors.white]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#ef9a9a')),
        ('PADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elems.append(t2)
    return elems


# ─────────────────────────────────────────────────────────────────
# Header / Footer callback
# ─────────────────────────────────────────────────────────────────
def header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4

    # Header
    canvas.setFillColor(colors.HexColor('#1565C0'))
    canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawString(18, h - 18, "RTL to GDSII — Complete ASIC Implementation Guide")
    canvas.drawRightString(w - 18, h - 18, "AND Gate Design | 45nm GPDK | Cadence EDA")

    # Footer
    canvas.setFillColor(colors.HexColor('#e3f2fd'))
    canvas.rect(0, 0, w, 20, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor('#1565C0'))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(18, 6, "Cadence: Xcelium · Genus · Conformal LEC · Innovus · PVS")
    canvas.drawRightString(w - 18, 6, f"Page {doc.page}")
    canvas.restoreState()


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────
def main():
    import os
    os.makedirs("output", exist_ok=True)
    out_path = "RTL_to_GDSII_AND_Gate_Guide.pdf"

    doc = SimpleDocTemplate(
        out_path,
        pagesize=A4,
        topMargin=1.8*cm,
        bottomMargin=1.2*cm,
        leftMargin=1.6*cm,
        rightMargin=1.6*cm,
        title="RTL to GDSII — AND Gate — Complete Cadence Flow",
        author="ASIC Design Flow Guide",
        subject="RTL to GDSII using Cadence Xcelium, Genus, Innovus, PVS"
    )

    styles = make_styles()
    story = []

    story += cover_page(styles)
    story += flow_diagram(styles)
    story += rtl_section(styles)
    story += tb_section(styles)
    story += sdc_section(styles)
    story += synthesis_section(styles)
    story += lec_section(styles)
    story += mmmc_section(styles)
    story += innovus_section(styles)
    story += rc_signoff_section(styles)
    story += pvs_section(styles)
    story += gds_section(styles)
    story += cheatsheet_section(styles)

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generated: {out_path}")


if __name__ == "__main__":
    main()
