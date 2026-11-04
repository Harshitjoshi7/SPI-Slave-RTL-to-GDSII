// =============================================================================
// Testbench : and_gate_tb
// Desc      : Exhaustive self-checking testbench for 2-input AND gate
//             Covers all 4 input combinations (truth table)
// =============================================================================

`timescale 1ns/1ps

module and_gate_tb;

    // -----------------------------------------------------------------------
    // DUT signals
    // -----------------------------------------------------------------------
    reg  a, b;
    wire y;

    // -----------------------------------------------------------------------
    // DUT instantiation
    // -----------------------------------------------------------------------
    and_gate uut (
        .a (a),
        .b (b),
        .y (y)
    );

    // -----------------------------------------------------------------------
    // Test tracking
    // -----------------------------------------------------------------------
    integer pass_cnt = 0;
    integer fail_cnt = 0;

    // -----------------------------------------------------------------------
    // Check task
    // -----------------------------------------------------------------------
    task check;
        input exp;
        input [63:0] label;
        begin
            #1;   // small propagation delay
            if (y === exp) begin
                pass_cnt = pass_cnt + 1;
                $display("[PASS] %0s | a=%b b=%b → y=%b (expected %b)",
                         label, a, b, y, exp);
            end else begin
                fail_cnt = fail_cnt + 1;
                $display("[FAIL] %0s | a=%b b=%b → y=%b (expected %b)",
                         label, a, b, y, exp);
            end
        end
    endtask

    // -----------------------------------------------------------------------
    // Stimulus – Truth Table
    //   A  B  |  Y
    //   0  0  |  0
    //   0  1  |  0
    //   1  0  |  0
    //   1  1  |  1
    // -----------------------------------------------------------------------
    initial begin
        $display("===========================================");
        $display("  AND Gate Testbench – Starting");
        $display("===========================================");

        // Apply all 4 input combinations
        a = 0; b = 0; check(1'b0, "0 AND 0");
        a = 0; b = 1; check(1'b0, "0 AND 1");
        a = 1; b = 0; check(1'b0, "1 AND 0");
        a = 1; b = 1; check(1'b1, "1 AND 1");

        $display("===========================================");
        $display("  Results: %0d PASSED, %0d FAILED", pass_cnt, fail_cnt);
        if (fail_cnt == 0)
            $display("  >>> ALL TESTS PASSED <<<");
        else
            $display("  >>> SOME TESTS FAILED <<<");
        $display("===========================================");
        $finish;
    end

endmodule

