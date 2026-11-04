// =============================================================================
// Module  : and_gate
// Desc    : 2-input AND gate - simple combinational RTL
// Ports   :
//   a  - Input A
//   b  - Input B
//   y  - Output Y = A & B
// =============================================================================

module and_gate (
    input  wire a,
    input  wire b,
    output wire y
);
    assign y = a & b;   // Single continuous assignment → synthesizes to AND2 cell
endmodule

