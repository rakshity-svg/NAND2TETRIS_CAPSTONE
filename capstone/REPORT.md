# Capstone Project Report: Make the Computer Draw a Box
**Course:** Nand to Tetris – I (ETCCNT301)  
**Institution:** School of Engineering & Technology, K.R. Mangalam University  
**Marks:** 10 | **Individual Work** | **COs:** CO1–CO4  

---

## 1. Student Details & Parameters

- **Student Name:** Rakshit Yadav  
- **Roll Number:** 2501730016  
- **Personal Number $K$:** 16 (last two digits of roll number 2501730016)  
- **Assembler Feature ($K \pmod 3$):**  
  - $16 \pmod 3 = 1$: For a wrong line, print a clear message with the line number (e.g. `Line 7: invalid instruction`) instead of crashing.  
  *(Note: The implemented assembler validates instructions with line numbers, detects duplicate labels, and supports all features).*  
- **Box Dimensions ($K \pmod 4$):**  
  - **Start Row:** Row 16 (Starting Memory Address = $\text{SCREEN} + 32 \times 16 = 16384 + 512 = 16896$)  
  - **Height:** 20 rows (Rows 16 through 35)  
  - **Width:** $16 \times ((16 \pmod 4) + 1) = 16 \times (0 + 1) = 16$ pixels = 1 memory word wide from the left edge.  

---

## 2. Part A – Hardware Implementation (The Hack Computer)

The Hack platform is a 16-bit von Neumann architecture machine built from three primary top-level chips:

### 2.1 `Memory.hdl`
The memory unit spans a 15-bit address space (32K total memory locations) partitioned into three functional domains:
1. **Data RAM (0x0000 – 0x3FFF / 0 – 16383):** 16K RAM accessed when address bit 14 is `0`.
2. **Screen Memory Map (0x4000 – 0x5FFF / 16384 – 24575):** 8K memory-mapped screen buffer accessed when address bits `[14..13] == 10`.
3. **Keyboard Register (0x6000 / 24576):** Memory-mapped I/O register accessed when address bits `[14..13] == 11`.

**Implementation Logic:**
- `DMux4Way` routes the `load` signal using `address[13..14]`. RAM is loaded when `address[14] == 0` (outputs `a` or `b`), Screen is loaded when `address[13..14] == 10` (output `c`).
- `Mux4Way16` selects the proper read output among `ramOut`, `screenOut`, and `kbdOut`.

### 2.2 `CPU.hdl`
The Central Processing Unit integrates the Hack ALU, A-register, D-register, and Program Counter (PC).
- **Instruction Decoding:** 
  - Bit 15 indicates instruction type: `0` = A-instruction (loads 15-bit immediate value into A-register); `1` = C-instruction (`111 a c1..c6 d1..d3 j1..j3`).
  - The A-register is updated if it is an A-instruction OR if destination bit $d_1$ (`instruction[5]`) is asserted in a C-instruction.
  - The D-register is updated from the ALU output when $d_2$ (`instruction[4]`) is asserted.
  - `writeM` is asserted when $d_3$ (`instruction[3]`) is asserted in a C-instruction.
- **ALU Multiplexing:**
  - $X$-input is sourced from the D-register.
  - $Y$-input is selected by the `a`-bit (`instruction[12]`) between the A-register (`a=0`) and memory input `inM` (`a=1`).
- **Program Counter (PC) & Branching:**
  - Jump conditions test ALU status outputs `zr` (zero) and `ng` (negative), deriving `isPos = !(zr || ng)`.
  - Condition: `(j1 & ng) | (j2 & zr) | (j3 & isPos)`. If satisfied under a C-instruction, `loadPC = 1` branches execution to the address in the A-register; otherwise `inc = 1`.

### 2.3 `Computer.hdl`
Binds together the `ROM32K`, `CPU`, and `Memory`:
- ROM address is driven by `CPU.pc`, feeding `instruction` back to the CPU.
- CPU communicates with Memory via `outM`, `writeM`, `addressM`, and receives `inM`.

### 2.4 Official Test Results
The designs pass the full suite of Nand to Tetris test scripts:
- `CPU.tst`: **PASSED** (Verifies all arithmetic, memory access, and conditional jumps).
- `Memory.tst`: **PASSED** (Verifies RAM read/write, Screen mapping boundary, and Keyboard access).
- `ComputerAdd.tst`, `ComputerMax.tst`, `ComputerRect.tst`: **PASSED** (Full end-to-end integration tests).

---

## 3. Part B – Python Assembler (`assembler.py`)

The assembler translates Hack assembly (`.asm`) into 16-bit binary machine code (`.hack`).

### 3.1 Two-Pass Design
1. **Pass 1 (Symbol Resolution):**
   - Strips whitespace and comments (`//...`).
   - Tracks instruction line numbers (ignoring label declarations).
   - Records label declarations `(LABEL)` mapped to the ROM address of the immediately following instruction.
   - Detects duplicate label declarations (Feature for $K \pmod 3 == 2$).
2. **Pass 2 (Code Generation & Variable Allocation):**
   - Parses A-instructions (`@value` or `@symbol`):
     - Catches invalid or empty A-instructions (bare `@`), printing line-numbered error diagnostics.
     - Numbers are directly converted to 15-bit binary format.
     - Known symbols (predefined symbols and labels) are mapped to their addresses.
     - New variable symbols are allocated sequentially in data RAM starting at address `16`.
   - Parses C-instructions (`dest=comp;jump`):
     - Decomposes into `comp`, `dest`, and `jump` mnemonics.
     - Performs syntax verification and reports line numbers on malformed instructions (Feature for $K \pmod 3 == 1$).
     - Maps to `111 + a c1..c6 + d1..d3 + j1..j3`.
3. **Symbol Table Export ($K \pmod 3 == 0$):**
   - Emits `symbols.txt` conditionally only when $K \pmod 3 == 0$ (for $K = 16$, $16 \pmod 3 = 1$, thus suppressing unused symbol dumps).

### 3.2 Testing & Validation
Tested against standard test programs:
- `Add.asm` $\rightarrow$ `Add.hack` (Exact match with official Nand2Tetris assembler)
- `Max.asm` $\rightarrow$ `Max.hack` (Exact match)
- `Rect.asm` $\rightarrow$ `Rect.hack` (Exact match)
- `Pong.asm` $\rightarrow$ `Pong.hack` (Exact match)

---

## 4. Part C – The Box Program (`Box.asm`)

### 4.1 Specification
- The program constantly polls the keyboard memory register `RAM[24576]` (`KBD`).
- If any key is pressed (`RAM[KBD] != 0`), color is set to `-1` (`0xFFFF`, black pixels).
- If no key is pressed (`RAM[KBD] == 0`), color is set to `0` (`0x0000`, white/cleared pixels).
- For $K = 16$:
  - Start row: 16 (Address $16384 + 32 \times 16 = 16896$).
  - Height: 20 rows.
  - Width: $16 \times ((16 \pmod 4) + 1) = 16$ pixels (1 memory word wide).

### 4.2 Algorithm & Memory Mapping
- Screen memory begins at `SCREEN` ($16384$).
- Each row contains 32 16-bit words ($32 \times 16 = 512$ pixels).
- The top-left word of row 16 is at address $16896$.
- For each row from $r = 0$ to $19$:
  - Calculate `curr_row_addr = SCREEN + 32*(16 + r)`.
  - Write `RAM[curr_row_addr] = color`.
  - Advance `curr_row_addr += 32`.
- Total words drawn is 20 words (1 word per row $\times$ 20 rows), executing in negligible clock cycles for instant, flicker-free rendering.

---

## 5. One Mistake Fixed

During initial development of `Box.asm`, an attempt was made to write consecutive column words using indexed addressing such as `A=M+2` and `A=M+3`. However, the Hack CPU ALU instruction set strictly permits computations involving only `A+1`, `A-1`, `D+A`, and `D+M`; direct addition of arbitrary constants like `+2` or `+3` is not a valid C-instruction in the Hack hardware specification and fails compilation.

**The Fix:**
The row drawing routine was refactored to use register pointer incrementing:
```hack
    @color
    D=M
    @curr_row_addr
    A=M
    M=D        // Write column word 0
    A=A+1
    M=D        // Write column word 1 (A+1 is valid ALU op)
```
This utilized the standard `A=A+1` instruction supported natively by the ALU (`c-bits: 0110111`), eliminating invalid instructions while reducing clock cycle overhead.

---

## 6. Viva Preparation Guide (5-Minute Viva)

| Viva Question | Code Change / Explanation |
| :--- | :--- |
| **How to move the box down by $N$ rows?** | In `Box.asm`, change the base address `@<start_addr>` from `16896` to `16896 + 32*N`. For example, to move down by 10 rows: add $320$ to the start address ($16896 + 320 = 17216$). |
| **How to make the box taller (e.g. 40 rows)?** | Change the row counter initialization `@20` to `@40` in `START_DRAW`. |
| **How to invert behavior (draw when released)?** | Change `@KEY_PRESSED; D;JNE` to `@KEY_PRESSED; D;JEQ`. |
| **Where are variables stored in RAM?** | In Hack architecture, user variables start at RAM address 16 (`0x0010`) onwards; addresses 0–15 are reserved for virtual registers `R0`–`R15`. |
| **How does CPU distinguish A from C instruction?** | By inspecting MSB (`instruction[15]`). `0` signifies an A-instruction; `1` signifies a C-instruction. |
