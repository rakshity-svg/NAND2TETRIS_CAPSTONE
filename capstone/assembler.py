#!/usr/bin/env python3
"""
Hack Assembler for Nand to Tetris (ETCCNT301 Capstone Project)
Translates Hack assembly programs (.asm) into Hack machine code (.hack).

Features:
- Two-pass assembler (handles forward labels and dynamic variables)
- Standard predefined symbols (R0-R15, SP, LCL, ARG, THIS, THAT, SCREEN, KBD)
- Extra features for K:
  * K mod 3 == 0: Exports symbols and variables to symbols.txt
  * K mod 3 == 1: Detailed error handling with line numbers (Line X: invalid instruction)
  * K mod 3 == 2: Duplicate label definition warning
"""

import sys
import os
import argparse

PREDEFINED_SYMBOLS = {
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576,
    **{f"R{i}": i for i in range(16)}
}

COMP_TABLE = {
    "0":   "0101010",
    "1":   "0111111",
    "-1":  "0111010",
    "D":   "0001100",
    "A":   "0110000",
    "!D":  "0001101",
    "!A":  "0110001",
    "-D":  "0001111",
    "-A":  "0110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "D+A": "0000010",
    "D-A": "0010011",
    "A-D": "0000111",
    "D&A": "0000000",
    "D|A": "0010101",
    "M":   "1110000",
    "!M":  "1110001",
    "-M":  "1110011",
    "M+1": "1110111",
    "M-1": "1110010",
    "D+M": "1000010",
    "D-M": "1010011",
    "M-D": "1000111",
    "D&M": "1000000",
    "D|M": "1010101"
}

DEST_TABLE = {
    "":    "000",
    "M":   "001",
    "D":   "010",
    "MD":  "011",
    "A":   "100",
    "AM":  "101",
    "AD":  "110",
    "AMD": "111"
}

JUMP_TABLE = {
    "":    "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111"
}


def clean_line(raw_line: str) -> str:
    """Strip comments and surrounding whitespace."""
    comment_idx = raw_line.find("//")
    if comment_idx != -1:
        raw_line = raw_line[:comment_idx]
    return raw_line.strip()


class Assembler:
    def __init__(self, k_val: int = 16):
        self.k_val = 16 if k_val is None else k_val
        self.symbol_table = dict(PREDEFINED_SYMBOLS)
        self.labels = {}
        self.variables = {}
        self.next_var_addr = 16

    def assemble(self, asm_filepath: str, output_filepath: str = None) -> bool:
        if not os.path.exists(asm_filepath):
            print(f"Error: File '{asm_filepath}' not found.")
            return False

        with open(asm_filepath, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()

        # Pass 1: Build symbol table for labels, record source line numbers
        rom_address = 0
        parsed_instructions = []  # list of (source_line_num, cleaned_text)
        has_errors = False

        for line_num, raw in enumerate(raw_lines, start=1):
            line = clean_line(raw)
            if not line:
                continue

            if line.startswith("(") and line.endswith(")"):
                label = line[1:-1].strip()
                if not label:
                    print(f"Line {line_num}: invalid instruction (empty label)")
                    has_errors = True
                    continue

                if label in self.symbol_table:
                    # Duplicate label warning (Feature K mod 3 == 2)
                    print(f"Warning: Line {line_num}: label '({label})' is already defined with address {self.symbol_table[label]}")
                else:
                    self.symbol_table[label] = rom_address
                    self.labels[label] = rom_address
            else:
                parsed_instructions.append((line_num, line))
                rom_address += 1

        # Pass 2: Translate instructions to machine code
        hack_instructions = []

        for line_num, line in parsed_instructions:
            if line.startswith("@"):
                # A-instruction
                symbol_or_val = line[1:].strip()
                if not symbol_or_val:
                    print(f"Line {line_num}: invalid instruction (empty @ instruction)")
                    has_errors = True
                    continue

                if symbol_or_val.isdigit():
                    addr = int(symbol_or_val)
                    if addr > 32767:
                        print(f"Line {line_num}: invalid instruction: constant {addr} exceeds 15-bit address space")
                        has_errors = True
                        continue
                else:
                    # Valid symbol identifier check
                    if symbol_or_val not in self.symbol_table:
                        self.symbol_table[symbol_or_val] = self.next_var_addr
                        self.variables[symbol_or_val] = self.next_var_addr
                        self.next_var_addr += 1
                    addr = self.symbol_table[symbol_or_val]

                binary = format(addr, "016b")
                hack_instructions.append(binary)

            else:
                # C-instruction: dest=comp;jump
                dest_part = ""
                comp_part = line
                jump_part = ""

                if "=" in comp_part:
                    dest_part, comp_part = comp_part.split("=", 1)
                    dest_part = dest_part.strip()

                if ";" in comp_part:
                    comp_part, jump_part = comp_part.split(";", 1)
                    jump_part = jump_part.strip()

                comp_part = comp_part.strip().replace(" ", "")

                # Normalize commutative operations if needed
                if comp_part not in COMP_TABLE:
                    if comp_part == "A+D":
                        comp_part = "D+A"
                    elif comp_part == "M+D":
                        comp_part = "D+M"
                    elif comp_part == "A&D":
                        comp_part = "D&A"
                    elif comp_part == "M&D":
                        comp_part = "D&M"
                    elif comp_part == "A|D":
                        comp_part = "D|A"
                    elif comp_part == "M|D":
                        comp_part = "D|M"

                # Validation with clear line numbers (Feature K mod 3 == 1)
                valid = True
                if comp_part not in COMP_TABLE:
                    print(f"Line {line_num}: invalid instruction: unrecognized comp '{comp_part}'")
                    valid = False
                if dest_part not in DEST_TABLE:
                    print(f"Line {line_num}: invalid instruction: unrecognized dest '{dest_part}'")
                    valid = False
                if jump_part not in JUMP_TABLE:
                    print(f"Line {line_num}: invalid instruction: unrecognized jump '{jump_part}'")
                    valid = False

                if not valid:
                    has_errors = True
                    continue

                comp_bits = COMP_TABLE[comp_part]
                dest_bits = DEST_TABLE[dest_part]
                jump_bits = JUMP_TABLE[jump_part]
                binary = "111" + comp_bits + dest_bits + jump_bits
                hack_instructions.append(binary)

        if has_errors:
            print("Assembly failed due to invalid instructions.")
            return False

        # Output filepath
        if output_filepath is None:
            base, _ = os.path.splitext(asm_filepath)
            output_filepath = base + ".hack"

        with open(output_filepath, "w", encoding="utf-8") as f:
            for instr in hack_instructions:
                f.write(instr + "\n")

        print(f"Successfully assembled '{asm_filepath}' -> '{output_filepath}' ({len(hack_instructions)} instructions).")

        # Extra feature: Save symbols.txt ONLY if K mod 3 == 0 (Feature K mod 3 == 0)
        if self.k_val is not None and (self.k_val % 3 == 0):
            symbols_filepath = os.path.join(os.path.dirname(output_filepath) or ".", "symbols.txt")
            self.save_symbols(symbols_filepath)

        return True

    def save_symbols(self, filepath: str):
        """Save all labels and variables with their addresses in symbols.txt."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("=== SYMBOLS TABLE (Labels & Variables) ===\n")
            f.write(f"{'SYMBOL':<20} {'TYPE':<12} {'ADDRESS (DEC)':<15} {'ADDRESS (HEX)':<15}\n")
            f.write("-" * 62 + "\n")

            # Sort symbols by address
            sorted_symbols = sorted(self.symbol_table.items(), key=lambda item: (item[1], item[0]))
            for sym, addr in sorted_symbols:
                if sym in PREDEFINED_SYMBOLS:
                    sym_type = "PREDEFINED"
                elif sym in self.labels:
                    sym_type = "LABEL (ROM)"
                elif sym in self.variables:
                    sym_type = "VAR (RAM)"
                else:
                    sym_type = "OTHER"
                f.write(f"{sym:<20} {sym_type:<12} {addr:<15} 0x{addr:04X}\n")

        print(f"Saved symbol table to '{filepath}'.")


def main():
    parser = argparse.ArgumentParser(description="Hack Computer Assembler (Nand to Tetris)")
    parser.add_argument("asm_file", help="Path to input .asm file")
    parser.add_argument("-o", "--output", help="Path to output .hack file (optional)")
    parser.add_argument("-k", "--k_val", type=int, default=16, help="Personal number K (default: 16)")

    args = parser.parse_args()
    assembler = Assembler(k_val=args.k_val)
    success = assembler.assemble(args.asm_file, args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
