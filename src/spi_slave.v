//=============================================================================
// Module: spi_slave
// Description: 4-wire synchronous SPI Slave with:
//   - 2-flop CDC synchronizers on SCK, CSB, MOSI
//   - Control FSM: IDLE -> FIRSTCYCLE -> WAITSECONDCYCLE ->
//                  SECONDCYCLEWRITE / SECONDCYCLEREAD -> END
//   - 8-bit serial-to-parallel shift register (SPI_received)
//   - 8-bit parallel-to-serial shift register (SPI_out)
//   - 4 internal 8-bit registers: decelerate, velocity, rotation, acceleration
//   - CPOL=0, CPHA=0 (SPI Mode 0)
//
// Port List:
//   clock   - System clock (internal domain)
//   resetb  - Active-low asynchronous reset
//   SCK     - SPI serial clock from master
//   CSB     - Active-low chip select from master
//   MOSI    - Master Out Slave In data
//   MISO    - Master In Slave Out data
//=============================================================================

module spi_slave (
    input  wire       clock,      // System clock
    input  wire       resetb,     // Active-low asynchronous reset
    input  wire       SCK,        // SPI serial clock (from master)
    input  wire       CSB,        // Active-low chip select (from master)
    input  wire       MOSI,       // Master Out Slave In
    output reg        MISO        // Master In Slave Out
);

    //=========================================================================
    // Parameter Definitions
    //=========================================================================

    // FSM State Encoding (one-hot for better synthesis & timing)
    localparam [5:0] IDLE             = 6'b000001;
    localparam [5:0] FIRSTCYCLE       = 6'b000010;
    localparam [5:0] WAITSECONDCYCLE  = 6'b000100;
    localparam [5:0] SECONDCYCLEWRITE = 6'b001000;
    localparam [5:0] SECONDCYCLEREAD  = 6'b010000;
    localparam [5:0] END              = 6'b100000;

    // Register Address Map (bits [1:0] of command byte)
    localparam [1:0] ADDR_DECELERATE   = 2'b00;
    localparam [1:0] ADDR_VELOCITY     = 2'b01;
    localparam [1:0] ADDR_ROTATION     = 2'b10;
    localparam [1:0] ADDR_ACCELERATION = 2'b11;

    // Command Byte Format:
    //   bit[7]   = R/W (1 = Read, 0 = Write)
    //   bit[6:2] = Reserved
    //   bit[1:0] = Register Address

    //=========================================================================
    // 2-Flop CDC Synchronizers (SCK, CSB, MOSI into system clock domain)
    //=========================================================================
    reg  SCK_sync1,  SCK_sync2;
    reg  CSB_sync1,  CSB_sync2;
    reg  MOSI_sync1, MOSI_sync2;

    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            SCK_sync1  <= 1'b0;
            SCK_sync2  <= 1'b0;
            CSB_sync1  <= 1'b1;   // CSB is active-low; default deasserted
            CSB_sync2  <= 1'b1;
            MOSI_sync1 <= 1'b0;
            MOSI_sync2 <= 1'b0;
        end else begin
            SCK_sync1  <= SCK;
            SCK_sync2  <= SCK_sync1;
            CSB_sync1  <= CSB;
            CSB_sync2  <= CSB_sync1;
            MOSI_sync1 <= MOSI;
            MOSI_sync2 <= MOSI_sync1;
        end
    end

    //=========================================================================
    // SCK Edge Detection (in system clock domain)
    //=========================================================================
    reg SCK_sync2_d;  // Delayed version for edge detection

    always @(posedge clock or negedge resetb) begin
        if (!resetb)
            SCK_sync2_d <= 1'b0;
        else
            SCK_sync2_d <= SCK_sync2;
    end

    wire SCK_rising  = ( SCK_sync2) & (~SCK_sync2_d);  // Rising  edge of SCK
    wire SCK_falling = (~SCK_sync2) & ( SCK_sync2_d);  // Falling edge of SCK

    //=========================================================================
    // Internal Registers (4 x 8-bit)
    //=========================================================================
    reg [7:0] reg_decelerate;
    reg [7:0] reg_velocity;
    reg [7:0] reg_rotation;
    reg [7:0] reg_acceleration;

    //=========================================================================
    // SPI Shift Registers & Bit Counter
    //=========================================================================
    reg [7:0] SPI_received;   // Serial-to-parallel input shift register
    reg [7:0] SPI_out;        // Parallel-to-serial output shift register
    reg [2:0] bit_cnt;        // 3-bit counter for 8-bit transfers (0..7)

    //=========================================================================
    // Command Byte Storage
    //=========================================================================
    reg [7:0] cmd_reg;        // Latched command byte from first transfer cycle
    wire       cmd_rw   = cmd_reg[7];     // 1 = Read, 0 = Write
    wire [1:0] cmd_addr = cmd_reg[1:0];   // Register address

    //=========================================================================
    // FSM State Register
    //=========================================================================
    reg [5:0] state, next_state;

    //=========================================================================
    // FSM: Next State Logic (combinational)
    //=========================================================================
    always @(*) begin
        next_state = state;  // Default: hold current state

        case (state)
            IDLE: begin
                // Wait for CSB to go low (transaction start)
                if (!CSB_sync2)
                    next_state = FIRSTCYCLE;
            end

            FIRSTCYCLE: begin
                // Shifting in the 8-bit command byte on SCK rising edges
                if (CSB_sync2)
                    next_state = IDLE;        // CSB deasserted → abort
                else if (SCK_rising && bit_cnt == 3'd7)
                    next_state = WAITSECONDCYCLE;
            end

            WAITSECONDCYCLE: begin
                // Command byte captured. Decide read or write.
                if (CSB_sync2)
                    next_state = IDLE;        // CSB deasserted → abort
                else if (SCK_falling) begin
                    // Transition on falling edge so data is set up for next rising
                    if (cmd_rw)
                        next_state = SECONDCYCLEREAD;
                    else
                        next_state = SECONDCYCLEWRITE;
                end
            end

            SECONDCYCLEWRITE: begin
                // Shifting in the 8-bit write data on SCK rising edges
                if (CSB_sync2)
                    next_state = IDLE;
                else if (SCK_rising && bit_cnt == 3'd7)
                    next_state = END;
            end

            SECONDCYCLEREAD: begin
                // Shifting out the 8-bit read data; count on rising edges
                // (master samples MISO on rising, so we count completed bits)
                if (CSB_sync2)
                    next_state = IDLE;
                else if (SCK_rising && bit_cnt == 3'd7)
                    next_state = END;
            end

            END: begin
                // Wait for CSB to go high (transaction complete)
                if (CSB_sync2)
                    next_state = IDLE;
            end

            default: begin
                next_state = IDLE;
            end
        endcase
    end

    //=========================================================================
    // FSM: State Register (sequential)
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb)
            state <= IDLE;
        else
            state <= next_state;
    end

    //=========================================================================
    // Bit Counter
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            bit_cnt <= 3'd0;
        end else begin
            case (state)
                IDLE: begin
                    bit_cnt <= 3'd0;
                end

                FIRSTCYCLE: begin
                    if (SCK_rising)
                        bit_cnt <= bit_cnt + 3'd1;
                end

                WAITSECONDCYCLE: begin
                    bit_cnt <= 3'd0;  // Reset for second byte
                end

                SECONDCYCLEWRITE: begin
                    if (SCK_rising)
                        bit_cnt <= bit_cnt + 3'd1;
                end

                SECONDCYCLEREAD: begin
                    if (SCK_rising)
                        bit_cnt <= bit_cnt + 3'd1;
                end

                END: begin
                    bit_cnt <= 3'd0;
                end

                default: bit_cnt <= 3'd0;
            endcase
        end
    end

    //=========================================================================
    // SPI Input Shift Register (MOSI → SPI_received)
    //   Samples MOSI on SCK rising edge (SPI Mode 0: CPOL=0, CPHA=0)
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            SPI_received <= 8'h00;
        end else begin
            if ((state == FIRSTCYCLE || state == SECONDCYCLEWRITE) && SCK_rising) begin
                SPI_received <= {SPI_received[6:0], MOSI_sync2};  // MSB first
            end
        end
    end

    //=========================================================================
    // Command Byte Latch
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            cmd_reg <= 8'h00;
        end else begin
            if (state == FIRSTCYCLE && SCK_rising && bit_cnt == 3'd7)
                cmd_reg <= {SPI_received[6:0], MOSI_sync2};  // Latch full cmd byte
        end
    end

    //=========================================================================
    // SPI Output Shift Register (SPI_out → MISO)
    //   Loads register data when WAITSECONDCYCLE detects read command
    //   Shifts data out MSB-first on SCK falling edge (after bit[7] is sent)
    //   Data flow: Load on WAITSECONDCYCLE, MISO drives [7] immediately,
    //              then shift left on each SCK falling in SECONDCYCLEREAD.
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            SPI_out <= 8'h00;
        end else begin
            if (state == WAITSECONDCYCLE && cmd_rw && SCK_falling) begin
                // Load the addressed register into SPI_out for read.
                // MISO will pick up SPI_out[7] on the next clock edge.
                case (cmd_addr)
                    ADDR_DECELERATE:   SPI_out <= reg_decelerate;
                    ADDR_VELOCITY:     SPI_out <= reg_velocity;
                    ADDR_ROTATION:     SPI_out <= reg_rotation;
                    ADDR_ACCELERATION: SPI_out <= reg_acceleration;
                    default:           SPI_out <= 8'h00;
                endcase
            end else if (state == SECONDCYCLEREAD && SCK_falling) begin
                // Shift left after each falling edge so next bit is ready.
                // bit_cnt counts on rising edges, so by the time the next
                // rising edge arrives, SPI_out[7] holds the correct bit.
                SPI_out <= {SPI_out[6:0], 1'b0};
            end
        end
    end

    //=========================================================================
    // MISO Output Driver
    //   Drives MSB of SPI_out during read phase; tri-state/zero otherwise.
    //   In SPI Mode 0, data changes on falling edge, sampled on rising edge.
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            MISO <= 1'b0;
        end else begin
            if (state == SECONDCYCLEREAD || 
                (state == WAITSECONDCYCLE && cmd_rw) ||
                (state == END && cmd_rw))
                MISO <= SPI_out[7];   // Drive MSB of shift register
            else
                MISO <= 1'b0;         // Default low when not reading
        end
    end

    //=========================================================================
    // Internal Register Write Logic
    //   Writes SPI_received to addressed register at end of write transaction
    //=========================================================================
    always @(posedge clock or negedge resetb) begin
        if (!resetb) begin
            reg_decelerate   <= 8'h00;
            reg_velocity     <= 8'h00;
            reg_rotation     <= 8'h00;
            reg_acceleration <= 8'h00;
        end else begin
            if (state == SECONDCYCLEWRITE && SCK_rising && bit_cnt == 3'd7) begin
                case (cmd_addr)
                    ADDR_DECELERATE:   reg_decelerate   <= {SPI_received[6:0], MOSI_sync2};
                    ADDR_VELOCITY:     reg_velocity     <= {SPI_received[6:0], MOSI_sync2};
                    ADDR_ROTATION:     reg_rotation     <= {SPI_received[6:0], MOSI_sync2};
                    ADDR_ACCELERATION: reg_acceleration <= {SPI_received[6:0], MOSI_sync2};
                    default: ; // No write
                endcase
            end
        end
    end

endmodule
