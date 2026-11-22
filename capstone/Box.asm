// Box.asm for K = 16
// Starts at row 16, 20 rows tall, and 16 pixels wide (W = 1 word).
// Screen row start address = 16384 + 32 * 16 = 16896
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

    // curr_row_addr = SCREEN + 32 * 16 = 16896
    @16896
    D=A
    @curr_row_addr
    M=D

(ROW_LOOP)
    // Check if row_count == 0
    @row_count
    D=M
    @MAIN_LOOP
    D;JEQ

    // Draw row words: W = 1
    // Column word 0
    @color
    D=M
    @curr_row_addr
    A=M
    M=D

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

