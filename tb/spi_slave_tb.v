//=============================================================================
// Testbench: spi_slave_tb
// Description: Self-checking testbench for spi_slave module
//   - 20 MHz system clock (50 ns period)
//   - SPI clock (SCK) at ~2 MHz (500 ns period) — slower than sys clock
//   - Tests:
//       1. Write to all 4 registers (decelerate, velocity, rotation, acceleration)
//       2. Read back all 4 registers and verify correctness
//       3. Write new values, then read back to confirm overwrite
//       4. CSB abort mid-transaction (coverage)
//       5. Back-to-back transactions (stress)
//=============================================================================

`timescale 1ns / 1ps

module spi_slave_tb;

    //=========================================================================
    // Clock & Reset Parameters
    //=========================================================================
    parameter SYS_CLK_PERIOD = 50;   // 20 MHz system clock → 50 ns period
    parameter SCK_HALF       = 250;  // SCK half-period → ~2 MHz (500 ns period)
    // SCK must be slower than system clock to guarantee CDC sampling

    //=========================================================================
    // DUT I/O
    //=========================================================================
    reg        clock;
    reg        resetb;
    reg        SCK;
    reg        CSB;
    reg        MOSI;
    wire       MISO;

    //=========================================================================
    // DUT Instantiation
    //=========================================================================
    spi_slave uut (
        .clock  (clock),
        .resetb (resetb),
        .SCK    (SCK),
        .CSB    (CSB),
        .MOSI   (MOSI),
        .MISO   (MISO)
    );

    //=========================================================================
    // System Clock Generation (20 MHz)
    //=========================================================================
    initial clock = 1'b0;
    always #(SYS_CLK_PERIOD / 2) clock = ~clock;

    //=========================================================================
    // Test Status Tracking
    //=========================================================================
    integer pass_count = 0;
    integer fail_count = 0;
    integer test_num   = 0;

    //=========================================================================
    // SPI Write Task
    //   Sends a WRITE command (bit[7]=0) with addr and then sends data byte.
    //   Total: 16 SCK cycles with CSB low.
    //=========================================================================
    task spi_write;
        input [1:0] addr;
        input [7:0] data;
        reg   [7:0] cmd_byte;
        integer i;
        begin
            cmd_byte = {1'b0, 5'b00000, addr};  // R/W=0 (write), addr

            // Assert CSB
            @(posedge clock);
            CSB  = 1'b0;
            #(SCK_HALF);

            // --- First Byte: Command ---
            for (i = 7; i >= 0; i = i - 1) begin
                // Set MOSI on falling edge (or before rising edge)
                MOSI = cmd_byte[i];
                #(SCK_HALF);
                SCK = 1'b1;         // Rising edge → slave samples MOSI
                #(SCK_HALF);
                SCK = 1'b0;         // Falling edge
            end

            // Small gap between command and data byte
            #(SCK_HALF);

            // --- Second Byte: Write Data ---
            for (i = 7; i >= 0; i = i - 1) begin
                MOSI = data[i];
                #(SCK_HALF);
                SCK = 1'b1;
                #(SCK_HALF);
                SCK = 1'b0;
            end

            // Deassert CSB
            #(SCK_HALF * 2);
            CSB  = 1'b1;
            MOSI = 1'b0;
            #(SCK_HALF * 4);   // Inter-transaction gap
        end
    endtask

    //=========================================================================
    // SPI Read Task
    //   Sends a READ command (bit[7]=1) with addr and then captures 8 bits
    //   from MISO.
    //=========================================================================
    task spi_read;
        input  [1:0] addr;
        output [7:0] read_data;
        reg    [7:0] cmd_byte;
        integer i;
        begin
            cmd_byte  = {1'b1, 5'b00000, addr};  // R/W=1 (read), addr
            read_data = 8'h00;

            // Assert CSB
            @(posedge clock);
            CSB  = 1'b0;
            #(SCK_HALF);

            // --- First Byte: Command ---
            for (i = 7; i >= 0; i = i - 1) begin
                MOSI = cmd_byte[i];
                #(SCK_HALF);
                SCK = 1'b1;
                #(SCK_HALF);
                SCK = 1'b0;
            end

            // Small gap → slave loads output shift register
            #(SCK_HALF);

            // --- Second Byte: Read Data ---
            // In our design: slave shifts MISO on SCK falling edge,
            // so data is stable for master to sample on the next rising edge.
            for (i = 7; i >= 0; i = i - 1) begin
                MOSI = 1'b0;  // Don't care during read
                #(SCK_HALF);
                SCK = 1'b1;
                // Sample MISO shortly after rising edge (data is stable)
                #(SYS_CLK_PERIOD * 2);
                read_data[i] = MISO;
                #(SCK_HALF - SYS_CLK_PERIOD * 2);
                SCK = 1'b0;
            end

            // Deassert CSB
            #(SCK_HALF * 2);
            CSB  = 1'b1;
            MOSI = 1'b0;
            #(SCK_HALF * 4);   // Inter-transaction gap
        end
    endtask

    //=========================================================================
    // Check Task
    //=========================================================================
    task check;
        input [7:0] expected;
        input [7:0] actual;
        input [8*32-1:0] test_name;
        begin
            test_num = test_num + 1;
            if (actual === expected) begin
                pass_count = pass_count + 1;
                $display("[PASS] Test %0d: %0s | Expected=0x%02h, Got=0x%02h",
                         test_num, test_name, expected, actual);
            end else begin
                fail_count = fail_count + 1;
                $display("[FAIL] Test %0d: %0s | Expected=0x%02h, Got=0x%02h",
                         test_num, test_name, expected, actual);
            end
        end
    endtask

    //=========================================================================
    // Main Test Sequence
    //=========================================================================
    reg [7:0] rdata;

    initial begin
        // ---- Initialization ----
        SCK    = 1'b0;
        CSB    = 1'b1;
        MOSI   = 1'b0;
        resetb = 1'b0;

        $display("=========================================");
        $display("  SPI Slave Testbench - Starting Tests");
        $display("=========================================");

        // Hold reset for several sys clock cycles
        #(SYS_CLK_PERIOD * 10);
        resetb = 1'b1;
        #(SYS_CLK_PERIOD * 5);

        // ============================================================
        //  TEST GROUP 1: Write all registers
        // ============================================================
        $display("\n--- Test Group 1: Write All Registers ---");

        spi_write(2'b00, 8'hA5);   // decelerate   = 0xA5
        spi_write(2'b01, 8'h3C);   // velocity      = 0x3C
        spi_write(2'b10, 8'hFF);   // rotation      = 0xFF
        spi_write(2'b11, 8'h42);   // acceleration  = 0x42

        // Verify via internal hierarchical access (for debug/coverage)
        check(8'hA5, uut.reg_decelerate,   "Write decelerate (hier)");
        check(8'h3C, uut.reg_velocity,     "Write velocity (hier)");
        check(8'hFF, uut.reg_rotation,     "Write rotation (hier)");
        check(8'h42, uut.reg_acceleration, "Write acceleration (hier)");

        // ============================================================
        //  TEST GROUP 2: Read all registers via SPI
        // ============================================================
        $display("\n--- Test Group 2: Read All Registers ---");

        spi_read(2'b00, rdata);
        check(8'hA5, rdata, "Read decelerate");

        spi_read(2'b01, rdata);
        check(8'h3C, rdata, "Read velocity");

        spi_read(2'b10, rdata);
        check(8'hFF, rdata, "Read rotation");

        spi_read(2'b11, rdata);
        check(8'h42, rdata, "Read acceleration");

        // ============================================================
        //  TEST GROUP 3: Overwrite and re-read
        // ============================================================
        $display("\n--- Test Group 3: Overwrite & Re-Read ---");

        spi_write(2'b00, 8'h11);   // decelerate   = 0x11
        spi_write(2'b01, 8'h22);   // velocity      = 0x22
        spi_write(2'b10, 8'h33);   // rotation      = 0x33
        spi_write(2'b11, 8'h44);   // acceleration  = 0x44

        spi_read(2'b00, rdata);
        check(8'h11, rdata, "Overwrite decelerate");

        spi_read(2'b01, rdata);
        check(8'h22, rdata, "Overwrite velocity");

        spi_read(2'b10, rdata);
        check(8'h33, rdata, "Overwrite rotation");

        spi_read(2'b11, rdata);
        check(8'h44, rdata, "Overwrite acceleration");

        // ============================================================
        //  TEST GROUP 4: Write 0x00 and 0xFF boundary
        // ============================================================
        $display("\n--- Test Group 4: Boundary Values ---");

        spi_write(2'b00, 8'h00);
        spi_read(2'b00, rdata);
        check(8'h00, rdata, "Boundary 0x00");

        spi_write(2'b00, 8'hFF);
        spi_read(2'b00, rdata);
        check(8'hFF, rdata, "Boundary 0xFF");

        // ============================================================
        //  TEST GROUP 5: CSB Abort (coverage - no check, just no hang)
        // ============================================================
        $display("\n--- Test Group 5: CSB Abort Mid-Transaction ---");

        @(posedge clock);
        CSB  = 1'b0;
        MOSI = 1'b1;
        #(SCK_HALF);
        SCK  = 1'b1;
        #(SCK_HALF);
        SCK  = 1'b0;
        // Abort: deassert CSB after only 1 SCK cycle
        #(SCK_HALF);
        CSB  = 1'b1;
        MOSI = 1'b0;
        #(SCK_HALF * 8);  // Wait for FSM to return to IDLE

        // Verify registers unchanged (should still be 0xFF from test group 4)
        spi_read(2'b00, rdata);
        check(8'hFF, rdata, "Post-abort decelerate unchanged");

        $display("[INFO] CSB abort test completed without hang.");

        // ============================================================
        //  Summary
        // ============================================================
        $display("\n=========================================");
        $display("  Test Summary: %0d PASSED, %0d FAILED (out of %0d)",
                 pass_count, fail_count, test_num);
        $display("=========================================");

        if (fail_count == 0)
            $display(">>> ALL TESTS PASSED <<<");
        else
            $display(">>> SOME TESTS FAILED <<<");

        #(SYS_CLK_PERIOD * 10);
        $finish;
    end

    //=========================================================================
    // Waveform Dump:
    // In Cadence Xcelium/Incisive, use '-waves' on command line for native SHM.
    // Legacy $dumpvars at T(0) triggers a known 'Stream rts_xfer' crash in xmsim.
    //=========================================================================
`ifdef DUMP_VCD
    initial begin
        $dumpfile("spi_slave_tb.vcd");
        $dumpvars(0, spi_slave_tb);
    end
`endif


endmodule
