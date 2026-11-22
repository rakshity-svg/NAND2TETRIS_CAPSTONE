#!/usr/bin/env python3
"""
Generator for Box.asm based on personal number K.
Starts at row K, height = 20, width = 16 * ((K mod 4) + 1) pixels.
"""

import sys

def generate_box_asm(k: int = 16) -> str:
    k_mod_4 = k % 4
    w = k_mod_4 + 1  # number of 16-bit words
    start_addr = 16384 + 32 * k
    pixels_wide = 16 * w

    asm_code = f"""// Box.asm for K = {k}
// Starts at row {k}, 20 rows tall, and {pixels_wide} pixels wide (W = {w} word{"s" if w > 1 else ""}).
// Screen row start address = 16384 + 32 * {k} = {start_addr}
// Draws black box (-1) when any key is pressed, white (0) when released.

(MAIN_LOOP)
    // Read keyboard
    @KBD
    D=M
    @KEY_PRESSED
    D;JNE

    // No key pressed -> color = 0 (white)
    @color
    M=0
    @START_DRAW
    0;JMP

(KEY_PRESSED)
    // Key pressed -> color = -1 (black)
    @color
    M=-1

(START_DRAW)
    // row_counter = 20
    @20
    D=A
    @row_count
    M=D

    // curr_row_addr = SCREEN + 32 * {k} = {start_addr}
    @{start_addr}
    D=A
    @curr_row_addr
    M=D

(ROW_LOOP)
    // Check if row_count == 0
    @row_count
    D=M
    @MAIN_LOOP
    D;JEQ

    // Draw row words: W = {w}
"""
    # Column word 0
    asm_code += """    // Column word 0
    @color
    D=M
    @curr_row_addr
    A=M
    M=D
"""
    for col in range(1, w):
        asm_code += f"""    // Column word {col}
    A=A+1
    M=D
"""

    asm_code += f"""
    // Advance to next row (+32 words)
    @32
    D=A
    @curr_row_addr
    M=M+D

    // Decrement row counter
    @row_count
    M=M-1

    @ROW_LOOP
    0;JMP
"""
    return asm_code

if __name__ == "__main__":
    k_val = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    print(generate_box_asm(k_val))
