# Pinky Column 7 (Branch `pinky-col7`): Status and Handoff

Last updated 2026-10-07 (UTC). Head `1fa790a`. Main is untouched.

## What Exists

- **Footprint:** `lib/footprints.pretty/SW_PG1316M_th_reversible_sucralose.kicad_mod` (on main, GPL-3.0, derived from dennisleexyz/libmodulo `SW_PG1316M` @5dbcd9b). The datasheet's 1.55x2 mm terminal lands at (+/-2.5, 0.7) are PTH with a 1.0 mm drill. The MP pads at (+/-6.35, +/-3.95) are duplicated F/B. Locating NPTHs at (+/-5.8, 0) are both 1.25 mm so either face fits. Courtyard is 16x10.3 mm (F-row keycap); the case guard is +0.5 mm, about 17.0x11.3 mm.
- **Datasheet and model:** `docs/PG1316M-datasheet.pdf`, `lib/3d/PG1316M.STEP`.
- **Strip:** 4x PG1316M, portrait (rot 9-90 = -81), at u=-17.5 in COL0's frame (origin = SW5 `C0 R1`, rot 9 deg), 17 mm pitch, centred in the strip.
  - Refs top to bottom: C6 R3 (D22, ROW3), C6 R0 (D23, ROW0), C6 R1 (D24, ROW1), C6 R2 (D25, ROW2).
  - Switch-to-diode nets: `pinky7_extra/top/home/bottom`.
  - COL6 goes to XIAO pad 17 (D13 = P1.01) on both copies. C6 R3 uses the free ROW3/COL6 matrix slot.
- **Breakaway:**
  - Four tabs of 0.6 mm NPTH perforations with a 0.35 mm web, plus 1.0 mm slots (the JLCPCB minimum NP slot).
  - The main-side slot wall lies on the Rev. 1 COL0 edge, so the snapped board keeps the Rev. 1 outline and corners and existing covers fit.
  - The strip spans the full board height, and its outer corners copy the main corner rounds. Inner corners are R1.5 (a larger radius would hit the MP copper).
  - Middle tabs carry the nets (3+3 holes around a copper channel). Dead-end stubs remain after a snap; file the edge.
- **DRC:** copper clean. The unconnected set matches main (7 display/battery ring pairs). Only new items are 8 `lib_footprint_issues` local-override warnings.

## Open Items

1. **ROW3 trace:** C6 R3's ROW3 trace runs diagonally across the C0 R0/R1 area on the top side. It's cosmetic. Jahn was offered a reroute along the edge or under the display; no decision yet.
2. **Firmware not updated:**
   - 7 columns: add COL6 = `&xiao_d 13` to the left/right overlays (the right is mirrored, so COL6 goes first) and `col-offset` = 7.
   - Matrix transform and keymap need the C6 positions (R0-R3).
3. **Keycap gap:** C6 keycaps sit about 4.3 mm from C0's; main columns are about 1 mm apart. Closing it pushes the switches into the slots.
4. **Not done yet:** cover/case model updates, a JLCPCB order check (confirm mouse bites and slots in the Gerber preview), and a physical snap test.

## How It Was Built (Scripts Are Gitignored, Local Only)

- `scripts/gen_pinky_col7.py`: start from `git show main:pcb/sucralose.kicad_pcb`. It places the switches, diodes, and mouse bites, rewrites the COL0 edge, and adds pad-17 COL6. It snaps new outline ends to existing ones and drops zero-length lines (KiCad `invalid_outline` otherwise).
- `scripts/route/route_col7.py`: run `extract_geom.py` first. It freezes existing copper, routes only the strip nets, and ties the diode back lands with vias. Takes about 1 minute.
- To verify: run DRC against `main` (`kicad-cli pcb drc`) and diff the category counts.
