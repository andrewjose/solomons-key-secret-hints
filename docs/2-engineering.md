# How Solomon's Key Secret Hints works

*Level 2 of 3: for software engineers who don't know game development or ROM hacking. The plain overview is [1-overview.md](1-overview.md). Exact addresses and byte layouts are in [3-technical.md](3-technical.md).*

## The starting point

An NES cartridge is two ROM chips and nothing else: **PRG**, the program (6502 machine code plus data), and **CHR**, the graphics (8×8-pixel tiles). There's no source code, no operating system and no file system. The game's code runs directly on a 1.79 MHz 6502 CPU with 2 KB of RAM. The patch edits the ROM image directly: a few bytes of existing code are changed to call new code, which goes into an unused part of the PRG chip.

Think of it as patching a tiny embedded firmware image with no symbols, where you must find free space yourself, because the binary can't grow.

The job came down to four problems.

## 1. Finding where secrets are stored

The game keeps the current room in RAM as a 16×12 grid, one byte per cell, like a 2D array of enums. The byte's value range says what the cell is:

| Byte value | Meaning |
| --- | --- |
| below `$40` | nothing special |
| `$40`–`$7F` | empty cell hiding an item, revealed by making a block there and breaking it |
| `$80`–`$F7` | brown block; it holds an item unless its low 6 bits are `$10` |
| `$F8` and up | white (unbreakable) block |

This layout comes partly from Kai E. Frøland's *Solomon's Key ROM map* and partly from tracing the game's code in a disassembler.

The key insight is that the game has *already* resolved the conditional secrets by the time this grid exists. If you broke the Seal chain, the Seal simply isn't written into the grid. So reading the grid as the room is drawn gives hints that are exactly right, with no need to reimplement the game's rules.

## 2. Marking a cell without new graphics slots

The NES draws the background from a grid of tile numbers (the *nametable*) that point into the CHR tile set. Each 16×16 room cell is four 8×8 tiles. There's no way to overlay a sprite on every secret cell: the NES can show only 8 sprites per scanline and 64 in total. So the marker has to be part of the background.

The approach:

- Find tile numbers the game never uses during play. A test script boots every one of the 53 rounds in an emulator and collects every tile number in each round's nametable. Anything absent from all of them is free.
- Into three free slots, draw copies of existing tiles with a ring added:
  - the background bricks;
  - the brown block;
  - the white block (needed for Bomb Jack in round 17).
- When the game builds a secret cell, swap its top-left tile for the ringed copy. The ring is drawn into that tile's bottom-right corner, so it ends up near the middle of the 16×16 cell.

The graphics come in four 8 KB banks, and the game switches between them (title screen versus gameplay). The ringed tiles are written into each of the three gameplay banks.

## 3. Hooking the room drawer

When a room is drawn, a loop calls a subroutine once per cell to fill a 4-byte buffer with that cell's four tile numbers. The patch changes the address in that one `JSR` (call) instruction so it calls a new routine instead. The new routine:

1. calls the original subroutine, so the buffer is filled exactly as before;
2. returns at once if hints are off;
3. reads the cell's byte from the room grid and classifies it as in the table above;
4. for a secret cell, overwrites the first byte of the buffer (the top-left tile) with the ringed tile number.

This is the wrapper or decorator pattern, done by editing one call target.

When a block is broken or created, the game redraws that cell through a different path that doesn't go through the hook. So the ring disappears on its own, exactly when the secret has been used. No extra bookkeeping is needed.

Bomb Jack is handled as a special case. His block isn't marked in the grid, so the routine checks for the two known (round, cell) pairs, gated on the same flag bit the game's own scripts test, and picks the ringed tile that matches whatever block is in that cell.

## 4. The off switch: a Konami code

The hints are off by default, so a single patch serves both players who want help and players who don't. The game reads the controller once per frame inside its vertical-blank interrupt handler (NMI). The patch redirects that call to a detector, which:

- calls the original controller read;
- runs only while the title screen's graphics bank is active (a second small hook records which bank the game just switched to);
- works out which buttons were *newly* pressed this frame (`current AND NOT previous`), so holding a button doesn't count twice;
- steps through the 10-button sequence, with the usual string-matching care for a repeated prefix. Pressing ↑ three times keeps you at step 2 instead of resetting to the start.

On success, it sets an enable flag in an unused RAM byte and plays one of the game's own sound effects. The flag is cleared when the console resets.

## Building and testing

- **Building.** `tools/build.py` is the whole build. It assembles the new routines with `py65`'s 6502 assembler, using a small two-pass label resolver. Before writing, it checks that every byte it is about to overwrite is what it expects: the original `JSR` targets, the bank-switch instructions, and free space that's all `$00` or `$FF`. Then it generates the ringed tiles and writes the patched ROM. The IPS patch is a diff between the original and the patched ROM.
- **Testing.** It runs headlessly in `cynes`, an NES emulator usable as a Python library. The test tools can force the game to start on any round by poking the starting-round byte, then boot it, dump the room grid from RAM and save screenshots. That makes it possible to check all 53 rounds without playing to them.
- **Reproducibility.** A from-source build is checked against a published CRC32 of the patched ROM.

## Trade-offs

- **Reading live game state instead of a hand-made list** costs a little more reverse engineering, but it means the hints can never disagree with the game, including the conditional Seal and bonus chains.
- **Marking with background tiles instead of sprites** avoids the NES sprite limits, but needs free tile slots and a ringed copy for each kind of tile a secret can sit on.
- **Off by default** makes the patch safe to give to anyone. The cost is that the code must be re-entered after every reset, because the cartridge has no save memory to remember it.
