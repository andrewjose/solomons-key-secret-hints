# Solomon's Key Secret Hints: what this hack does

*Level 1 of 3: plain-language overview. For software engineers: [2-engineering.md](2-engineering.md). For ROM hackers: [3-technical.md](3-technical.md).*

## The problem

*Solomon's Key* (Tecmo, NES, 1987) hides a lot of its best stuff:

- bonus items inside breakable brown blocks;
- bells, fairies, keys and the rare **Solomon's Seals** that only appear if you create a block on a particular empty spot and then break it;
- a hidden Bomb Jack you reveal by hitting one block 11 times.

Nothing on screen tells you where any of these are. Finding them means a guide open next to you, or a lot of trial and error. The Seals are the hardest to find, and the ones players most often look up.

## What the hack adds

On every tile hiding a secret, the hack draws a small ring. The ring is subtle and sits near the middle of the tile, so the level still looks like the original game.

- **A ring on a brown block** means something is inside it.
- **A ring on an empty spot** means you need to make a block there and break it.
- **A ring on Bomb Jack's block** (rounds 17 and 40) means it's the one to hit 11 times.

When you break a marked block, or make a block on a marked spot, the tile is drawn normally and the ring goes away.

## The rings are always right

The hack doesn't use a list of secrets copied from a guide. It reads the game's own room data as each room is drawn, so it only marks what the game will actually reveal:

- Seals are marked only when the Seal will really appear, so not after you've broken the Seal chain.
- Chained bonus items stop being marked once you've missed one, because the game stops placing them.
- Bomb Jack is marked only when the game's own condition for him is met.

## Turning it on

The hints are **off by default**, so the patched game plays exactly like the original until you ask for help. On the title screen, enter the Konami code **↑ ↑ ↓ ↓ ← → ← → B A**. You'll hear a sound to confirm it. The hints stay on until you reset or turn the console off.

## How to play it

Apply `patch/Solomons_Key_Secret_Hints.ips` to your own copy of *Solomon's Key (USA)*, using Flips, Lunar IPS or RomPatcher.js. The ROM must include its 16-byte header (the file is 65,552 bytes). The [README](../README.md) lists the checksum the patched game should have. It works in any NES emulator or on a flash cart.

## Limits

- Only the US release is supported.
- The hints can't be saved as "on". Enter the code again after a reset.
- No ROM data is included. You need your own copy of the game.
