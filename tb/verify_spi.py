"""
Proper cycle-accurate Verilog `<=` non-blocking model for spi_slave.
"""

class SpiSlaveVerilogModel:
    def __init__(self):
        self.resetb = 0
        self.clock = 0
        self.SCK = 0
        self.CSB = 1
        self.MOSI = 0
        self.MISO = 0

        # Flip-flops (current state Q)
        self.SCK_sync1 = 0
        self.SCK_sync2 = 0
        self.CSB_sync1 = 1
        self.CSB_sync2 = 1
        self.MOSI_sync1 = 0
        self.MOSI_sync2 = 0
        self.SCK_sync2_d = 0

        self.state = 1 # IDLE=1, FIRSTCYCLE=2, WAITSECONDCYCLE=4, SECONDCYCLEWRITE=8, SECONDCYCLEREAD=16, END=32
        self.bit_cnt = 0
        self.SPI_received = 0
        self.cmd_reg = 0
        self.SPI_out = 0

        self.reg_decelerate = 0
        self.reg_velocity = 0
        self.reg_rotation = 0
        self.reg_acceleration = 0

    def posedge_clock(self, SCK, CSB, MOSI, resetb):
        if not resetb:
            self.SCK_sync1 = 0
            self.SCK_sync2 = 0
            self.CSB_sync1 = 1
            self.CSB_sync2 = 1
            self.MOSI_sync1 = 0
            self.MOSI_sync2 = 0
            self.SCK_sync2_d = 0
            self.state = 1
            self.bit_cnt = 0
            self.SPI_received = 0
            self.cmd_reg = 0
            self.SPI_out = 0
            self.MISO = 0
            self.reg_decelerate = 0
            self.reg_velocity = 0
            self.reg_rotation = 0
            self.reg_acceleration = 0
            return self.MISO

        # In Verilog:
        # Combinational signals evaluate using current Q outputs:
        SCK_rising = (self.SCK_sync2 == 1) and (self.SCK_sync2_d == 0)
        SCK_falling = (self.SCK_sync2 == 0) and (self.SCK_sync2_d == 1)

        cmd_rw = (self.cmd_reg >> 7) & 1
        cmd_addr = self.cmd_reg & 0x03

        # Combinational next_state logic:
        next_state = self.state
        if self.state == 1: # IDLE
            if not self.CSB_sync2:
                next_state = 2 # FIRSTCYCLE
        elif self.state == 2: # FIRSTCYCLE
            if self.CSB_sync2:
                next_state = 1
            elif SCK_rising and self.bit_cnt == 7:
                next_state = 4 # WAITSECONDCYCLE
        elif self.state == 4: # WAITSECONDCYCLE
            if self.CSB_sync2:
                next_state = 1
            elif SCK_falling:
                if cmd_rw:
                    next_state = 16 # SECONDCYCLEREAD
                else:
                    next_state = 8 # SECONDCYCLEWRITE
        elif self.state == 8: # SECONDCYCLEWRITE
            if self.CSB_sync2:
                next_state = 1
            elif SCK_rising and self.bit_cnt == 7:
                next_state = 32 # END
        elif self.state == 16: # SECONDCYCLEREAD
            if self.CSB_sync2:
                next_state = 1
            elif SCK_rising and self.bit_cnt == 7:
                next_state = 32 # END
        elif self.state == 32: # END
            if self.CSB_sync2:
                next_state = 1
        else:
            next_state = 1

        # Next D values for flip-flops (evaluate concurrently):
        d_SCK_sync1 = SCK
        d_SCK_sync2 = self.SCK_sync1
        d_CSB_sync1 = CSB
        d_CSB_sync2 = self.CSB_sync1
        d_MOSI_sync1 = MOSI
        d_MOSI_sync2 = self.MOSI_sync1
        d_SCK_sync2_d = self.SCK_sync2

        d_state = next_state

        # bit_cnt D
        d_bit_cnt = self.bit_cnt
        if self.state == 1:
            d_bit_cnt = 0
        elif self.state == 2:
            if SCK_rising:
                d_bit_cnt = (self.bit_cnt + 1) & 7
        elif self.state == 4:
            d_bit_cnt = 0
        elif self.state == 8:
            if SCK_rising:
                d_bit_cnt = (self.bit_cnt + 1) & 7
        elif self.state == 16:
            if SCK_rising:
                d_bit_cnt = (self.bit_cnt + 1) & 7
        elif self.state == 32:
            d_bit_cnt = 0

        # SPI_received D
        d_SPI_received = self.SPI_received
        if (self.state in (2, 8)) and SCK_rising:
            d_SPI_received = ((self.SPI_received << 1) & 0xFE) | self.MOSI_sync2

        # cmd_reg D
        d_cmd_reg = self.cmd_reg
        if self.state == 2 and SCK_rising and self.bit_cnt == 7:
            d_cmd_reg = ((self.SPI_received << 1) & 0xFE) | self.MOSI_sync2

        # SPI_out D
        d_SPI_out = self.SPI_out
        if self.state == 4 and cmd_rw and SCK_falling:
            if cmd_addr == 0: d_SPI_out = self.reg_decelerate
            elif cmd_addr == 1: d_SPI_out = self.reg_velocity
            elif cmd_addr == 2: d_SPI_out = self.reg_rotation
            elif cmd_addr == 3: d_SPI_out = self.reg_acceleration
            else: d_SPI_out = 0
        elif self.state == 16 and SCK_falling:
            d_SPI_out = (self.SPI_out << 1) & 0xFE

        # MISO D
        d_MISO = 0
        if self.state == 16 or (self.state == 4 and cmd_rw) or (self.state == 32 and cmd_rw):
            d_MISO = (self.SPI_out >> 7) & 1
        else:
            d_MISO = 0

        # Internal registers D
        d_reg_dec = self.reg_decelerate
        d_reg_vel = self.reg_velocity
        d_reg_rot = self.reg_rotation
        d_reg_acc = self.reg_acceleration
        if self.state == 8 and SCK_rising and self.bit_cnt == 7:
            val = ((self.SPI_received << 1) & 0xFE) | self.MOSI_sync2
            if cmd_addr == 0: d_reg_dec = val
            elif cmd_addr == 1: d_reg_vel = val
            elif cmd_addr == 2: d_reg_rot = val
            elif cmd_addr == 3: d_reg_acc = val

        # Clock edge: latch all D inputs to Q registers simultaneously
        self.SCK_sync1 = d_SCK_sync1
        self.SCK_sync2 = d_SCK_sync2
        self.CSB_sync1 = d_CSB_sync1
        self.CSB_sync2 = d_CSB_sync2
        self.MOSI_sync1 = d_MOSI_sync1
        self.MOSI_sync2 = d_MOSI_sync2
        self.SCK_sync2_d = d_SCK_sync2_d
        self.state = d_state
        self.bit_cnt = d_bit_cnt
        self.SPI_received = d_SPI_received
        self.cmd_reg = d_cmd_reg
        self.SPI_out = d_SPI_out
        self.MISO = d_MISO
        self.reg_decelerate = d_reg_dec
        self.reg_velocity = d_reg_vel
        self.reg_rotation = d_reg_rot
        self.reg_acceleration = d_reg_acc

        return self.MISO


def run_full_suite():
    dut = SpiSlaveVerilogModel()
    SCK = 0
    CSB = 1
    MOSI = 0
    resetb = 1

    # Reset
    resetb = 0
    for _ in range(10): dut.posedge_clock(SCK, CSB, MOSI, resetb)
    resetb = 1
    for _ in range(10): dut.posedge_clock(SCK, CSB, MOSI, resetb)

    def write_reg(addr, data):
        nonlocal CSB, SCK, MOSI
        cmd_byte = (0 << 7) | (addr & 3)
        CSB = 0
        for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)

        # Byte 1: cmd
        for i in range(7, -1, -1):
            MOSI = (cmd_byte >> i) & 1
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 1
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 0

        for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)

        # Byte 2: data
        for i in range(7, -1, -1):
            MOSI = (data >> i) & 1
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 1
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 0

        for _ in range(10): dut.posedge_clock(SCK, CSB, MOSI, resetb)
        CSB = 1
        MOSI = 0
        for _ in range(20): dut.posedge_clock(SCK, CSB, MOSI, resetb)

    def read_reg(addr):
        nonlocal CSB, SCK, MOSI
        cmd_byte = (1 << 7) | (addr & 3)
        read_val = 0
        CSB = 0
        for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)

        # Byte 1: cmd
        for i in range(7, -1, -1):
            MOSI = (cmd_byte >> i) & 1
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 1
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 0

        for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)

        # Byte 2: read
        for i in range(7, -1, -1):
            MOSI = 0
            for _ in range(5): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 1
            # In testbench: sample after 2 clock cycles (100ns)
            for _ in range(3): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            bit = dut.MISO
            read_val = (read_val << 1) | bit
            for _ in range(2): dut.posedge_clock(SCK, CSB, MOSI, resetb)
            SCK = 0

        for _ in range(10): dut.posedge_clock(SCK, CSB, MOSI, resetb)
        CSB = 1
        MOSI = 0
        for _ in range(20): dut.posedge_clock(SCK, CSB, MOSI, resetb)
        return read_val

    print("--- Test 1 & 2: Write all 4 registers & Read back ---")
    vals = [0xA5, 0x3C, 0xF0, 0x5A]
    for a, v in enumerate(vals):
        write_reg(a, v)

    errs = 0
    for a, expected in enumerate(vals):
        actual = read_reg(a)
        status = "PASS" if actual == expected else "FAIL"
        print(f"Addr {a}: Expected=0x{expected:02X}, Actual=0x{actual:02X} -> [{status}]")
        if actual != expected: errs += 1

    print("\n--- Test 3: Overwrite all 4 registers & Read back ---")
    new_vals = [0x12, 0x34, 0x56, 0x78]
    for a, v in enumerate(new_vals):
        write_reg(a, v)

    for a, expected in enumerate(new_vals):
        actual = read_reg(a)
        status = "PASS" if actual == expected else "FAIL"
        print(f"Addr {a}: Expected=0x{expected:02X}, Actual=0x{actual:02X} -> [{status}]")
        if actual != expected: errs += 1

    print(f"\nTotal verification errors: {errs}")
    return errs

if __name__ == "__main__":
    import sys
    sys.exit(run_full_suite())
