# Solomon's Key Secret Hints: technical reference

*Level 3 of 3: for ROM hackers. Lower levels: [1-overview.md](1-overview.md), [2-engineering.md](2-engineering.md).*

`tools/build.py` is the primary record: it holds the full assembly source of both routines and every patch site with its assertion. This page documents the design and the addresses.

## Base ROM

- `Solomon's Key (USA).nes`, headered iNES, 65,552 bytes: 16-byte header + 32 KB PRG (`$8000`–`$FFFF`, unbanked) + 32 KB CHR (four 8 KB banks).
- File offset of PRG address `a` = `a − $8000 + $10`. CHR starts at file offset `$8010`.
- Background tiles are in each bank's second pattern table (`bank·$2000 + $1000`). Banks 0–2 are used in gameplay, and bank 3 is the title screen.
- The patched PRG+CHR (header skipped) has CRC32 `944491BA` with the default ring colors.

## Game data and RAM used

| Address | What |
| --- | --- |
| `$0300`–`$03FF` | room map; the playfield grid is `$0314` + `y·16 + x` (12 rows × 16 columns) |
| `$0304 + pos` | cell byte for item position byte `pos` (`x = pos & $0F`, `y = (pos >> 4) − 1`) |
| `$00` | current cell index during the bulk room draw |
| `$03E9`–`$03EC` | 4-tile buffer for the cell being drawn; `$03E9` is the top-left tile |
| `$0428` | current round, 0-based (`$10` = round 17, `$27` = round 40) |
| `$7C` | flags; the game's scripts gate Bomb Jack on bit 4 (`$10`) being clear |
| `$7D` | CHR bank control written in the NMI |
| `$82` | controller 1 buttons after the game's read (`A=$80 B=$40 Sel=$20 St=$10 U=$08 D=$04 L=$02 R=$01`) |

**Cell byte classes** (the marker's decision table):

| Byte | Meaning | Marker tile |
| --- | --- | --- |
| `< $40` | nothing hidden | none |
| `$40`–`$7F` | empty cell, item revealed by make-and-break (bells, fairies, keys, Seals) | `$98` |
| `$80`–`$F7`, `(b & $3F) ≠ $10` | brown block containing an item | `$25` |
| `$80`–`$F7`, `(b & $3F) = $10` | plain brown block | none |
| `≥ $F8` | white block | none (except Bomb Jack) |

Conditional secrets (the Seal chain, chained bonus items) are resolved by the game before the grid is filled. A suppressed secret simply isn't in the grid, so the marker needs no extra logic for them.

**Per-round item data** (`tools/parse.py`):

- The pointer table is at file `$6A2C`, split into 53 low bytes then 53 high bytes.
- Each round has a 10-byte header (byte 4 = key item, byte 6 = key position), followed by an item stream:
  - `$00` or `$E0`–`$EF`: end of stream.
  - `$F0`–`$FB nn`: end, with a constant.
  - `$C0`–`$DF`: a run of `c − $BF` items sharing the following code byte, then that many position bytes.
  - Otherwise, a `(code, pos)` pair.

## Patch sites

| PRG addr | Original | Patched | Purpose |
| --- | --- | --- | --- |
| `$96A6` | `20 21 9E` (`JSR $9E21`) | `20 00 B5` | bulk room drawer (`$9661`): per-cell tile builder → marker hook |
| `$80D2` | `20 7D 83` (`JSR $837D`) | `20 56 B5` | NMI controller read → Konami detector |
| `$8051` | `A9 80 85 7D` (`LDA #$80 / STA $7D`) | `20 9A B5 EA` | NMI CHR bank write → bank recorder |
| `$B500`–`$B5AB` | `$00`/`$FF` (asserted free) | 172 bytes | new code and data |

**CHR edits**, written into banks 0–2 (`tools/ring.py`):

| Tile | Copied from | Ring color (palette index) |
| --- | --- | --- |
| `$98` | `$2C` (background bricks) | `BGC`, default 2 (gray) |
| `$25` | `$90` (brown block, top-left) | `BLKC`, default 1 (dark) |
| `$27` | `$84` (white block, top-left) | 1 (dark) |

The tiles were chosen with `tools/survey.py`, which boots all 53 rounds and collects every tile index in each nametable. These three never appear during gameplay.

The ring is a 5×5 outline in the tile's bottom-right corner (rows 3–7, columns 3–7), so it sits just up and left of the 16×16 cell's center. Only the ring pixels change, and the rest of the source tile is copied as is.

## Marker routine (`$B500`–`$B555`)

```
hook:   JSR $9E21          ; original: fill $03E9-$03EC for cell $00
        LDA $07E0 : BEQ done   ; hints off
        LDX $00 : LDA $0304,X
        CMP #$F8 : BCS chkbj   ; white block
        CMP #$40 : BCC chkbj   ; nothing hidden
        CMP #$80 : BCC markbg  ; $40-$7F: make-and-break
        AND #$3F : CMP #$10 : BEQ chkbj   ; plain brown block
        BNE mark
markbg: LDA #$98 : BNE store
mark:   LDA #$25 : BNE store
markw:  LDA #$27
store:  STA $03E9 : RTS
chkbj:  LDA $7C : AND #$10 : BNE done
        LDA $0428
        CMP #$10 : BNE nxt : CPX #$7E : BEQ bj    ; round 17, pos $7E
nxt:    CMP #$27 : BNE done : CPX #$56 : BEQ bj   ; round 40, pos $56
done:   RTS
bj:     LDA $0304,X : CMP #$F8 : BCS markw : CMP #$80 : BCS mark : BCC markbg
```

- Only the bulk drawer is hooked. Single-cell redraws (breaking or creating a block) use the game's own path, so a used secret loses its ring with no state to track.
- The routine clobbers `A` and `X` (and flags) after the original call. The bulk-draw loop tolerates this, as the headless boots of every round show.

## Konami detector (`$B556`–`$B5AB`)

```
konami: JSR $837D                 ; original controller read
        LDA $07E3 : CMP #$03 : BNE kout   ; title-screen CHR bank only
        LDA $82 : TAY
        EOR $07E2 : AND $82       ; newly pressed = cur & ~prev
        STY $07E2 : BEQ kout
        LDX $07E1 : CMP kseq,X : BEQ kadv
        CMP #$08 : BNE kzero      ; mismatch: was it Up?
        CPX #$02 : BEQ kset       ; U,U,U stays at step 2
        LDX #$01 : BNE kset       ; otherwise Up restarts at step 1
kzero:  LDX #$00 : BEQ kset
kadv:   INX : CPX #$0A : BNE kset
        LDA #$01 : STA $07E0      ; enable hints
        LDY #$18 : JSR $8E8D      ; game's sound-effect call
        LDX #$00
kset:   STX $07E1
kout:   RTS
bankhook: STX $07E3 : LDA #$80 : STA $7D : RTS   ; X = bank the NMI is selecting
kseq:   .byte $08,$08,$04,$04,$02,$01,$02,$01,$40,$80
```

- Two simultaneous new presses never equal a single-bit sequence entry, so they reset the match. This is intended.
- New RAM: `$07E0` = enable flag, `$07E1` = sequence index, `$07E2` = previous buttons, `$07E3` = current CHR bank. The game doesn't use them. They're cleared on reset, which is why the hints are off after a reset.

## Build

- `build.py` assembles with `py65`. Its two-pass label resolver substitutes label addresses into the source text, with a placeholder pass for forward references.
- It asserts the three original instruction sequences and that `$B500`–`$B5AB` is all `$00`/`$FF` before writing.
- `ips.py` emits plain IPS records: runs of differing bytes, capped at `$FFFF` per record, with no RLE.

## Testing

- The `cynes` NES emulator runs headless from Python (`tools/emu.py`, `boot.py`). `boot()` taps Start through the title screen.
- `survey.py` forces the starting round by poking file offset `$1145` (PRG `$9135`) for each of the 53 rounds. It boots each one, saves a screenshot, and computes the set of unused BG tiles.
- `shots.py patched.nes out.png 17,40,...` tiles screenshots of chosen rounds for visual review.
- `boot.dumpmap` and `boot.grid` print the room map from RAM. They're for checking the cell classes against what a round really reveals.
- `parse.py` dumps every round's item stream, for cross-checking markers against the level data.
- The reference result is the CRC32 above. A from-source build must reproduce it with the default colors.

## Notes and limits

- Only the bulk room draw places rings. Any cell the game redraws through another path is drawn plain. That's what removes the ring when a secret is used, and it would also apply to any other single-cell redraw.
- Bomb Jack's two locations are hard-coded (round 17 pos `$7E`, round 40 pos `$56`), because he isn't encoded in the grid. The marker tile follows whatever block occupies the cell (white in round 17).
- The enable flag isn't persisted, because the cartridge has no save RAM.
- Credit: the item and level data layout comes from Kai E. Frøland's *Solomon's Key ROM map* (romhacking.net).
