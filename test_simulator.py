#!/usr/bin/env python3
"""
Lightweight Hack Computer & CPU Emulator in Python.
Used to test CPU logic, Memory mapping, and Box.hack execution.
"""

import sys

class HackSimulator:
    def __init__(self, rom_code):
        self.rom = rom_code + [0] * (32768 - len(rom_code))
        self.ram = [0] * 32768
        self.pc = 0
        self.a = 0
        self.d = 0

    def step(self):
        instr = self.rom[self.pc]
        next_pc = self.pc + 1

        if (instr & 0x8000) == 0:
            # A-instruction
            self.a = instr & 0x7FFF
        else:
            # C-instruction: 111 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
            a_bit = (instr >> 12) & 1
            comp_bits = (instr >> 6) & 0x3F
            d1 = (instr >> 5) & 1
            d2 = (instr >> 4) & 1
            d3 = (instr >> 3) & 1
            j1 = (instr >> 2) & 1
            j2 = (instr >> 1) & 1
            j3 = instr & 1

            x = self.d
            y = self.ram[self.a] if a_bit else self.a

            # Compute ALU
            zx = (comp_bits >> 5) & 1
            nx = (comp_bits >> 4) & 1
            zy = (comp_bits >> 3) & 1
            ny = (comp_bits >> 2) & 1
            f  = (comp_bits >> 1) & 1
            no = comp_bits & 1

            x_val = 0 if zx else x
            if nx:
                x_val = (~x_val) & 0xFFFF

            y_val = 0 if zy else y
            if ny:
                y_val = (~y_val) & 0xFFFF

            if f:
                out = (x_val + y_val) & 0xFFFF
            else:
                out = (x_val & y_val) & 0xFFFF

            if no:
                out = (~out) & 0xFFFF

            # Signed 16-bit interpretation
            signed_out = out if out < 0x8000 else out - 0x10000
            zr = 1 if out == 0 else 0
            ng = 1 if (out & 0x8000) != 0 else 0
            pos = 1 if (not zr and not ng) else 0

            # Write destinations
            if d1:
                self.a = out & 0x7FFF
            if d2:
                self.d = out
            if d3:
                self.ram[self.a] = out

            # Jump logic
            jump = (j1 and ng) or (j2 and zr) or (j3 and pos)
            if jump:
                next_pc = self.a

        self.pc = next_pc & 0x7FFF

    def run_cycles(self, n):
        for _ in range(n):
            self.step()


def test_box(hack_file, k):
    with open(hack_file) as f:
        code = [int(line.strip(), 2) for line in f if line.strip()]

    sim = HackSimulator(code)

    # 1. Run with key pressed (KBD = 65 -> 'A')
    sim.ram[24576] = 65
    sim.run_cycles(1500)

    w = (k % 4) + 1
    start_row = k
    start_addr = 16384 + 32 * k

    # Check that box area is black (0xFFFF = 65535)
    box_correct = True
    for r in range(20):
        for c in range(w):
            addr = 16384 + 32 * (k + r) + c
            val = sim.ram[addr]
            if val != 0xFFFF:
                print(f"Error at row {k+r}, col {c} (addr {addr}): expected 0xFFFF, got {val:#06x}")
                box_correct = False

    # Check outside box (e.g. word after box or row above)
    outside_correct = (sim.ram[start_addr + w] == 0)
    print(f"Key Pressed Test: Box pixels drawn correctly: {box_correct}")
    print(f"Key Pressed Test: Outside pixels untouched: {outside_correct}")

    # 2. Release key (KBD = 0)
    sim.ram[24576] = 0
    sim.run_cycles(1500)

    cleared = True
    for r in range(20):
        for c in range(w):
            addr = 16384 + 32 * (k + r) + c
            if sim.ram[addr] != 0:
                print(f"Error clearing at row {k+r}, col {c}: got {sim.ram[addr]:#06x}")
                cleared = False
    print(f"Key Released Test: Box pixels erased correctly: {cleared}")

    if box_correct and outside_correct and cleared:
        print(f"ALL TESTS PASSED FOR K = {k}!")
        return True
    return False

if __name__ == "__main__":
    k_test = int(sys.argv[1]) if len(sys.argv) > 1 else 41
    test_box("Box.hack", k_test)
