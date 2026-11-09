# MeshSlide-DualRF Release Versioning

**Current Active Version:** `v2.0` (configured via `MODEL_VERSION = "v2.0"` in [`cad/config.py`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/cad/config.py))

---

## `v2.0` (Current Release)
All active folders (`STL/`, `STEP/`, `3MF/`) contain **only** the `v2.0` release files:

### 1. Ready-to-Print 3MF Kits (`3MF/`)
- [`Top_Antenna_Rail_BoltOn_N_Only_v2.0.3mf`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/3MF/Top_Antenna_Rail_BoltOn_N_Only_v2.0.3mf) — Standalone single-part 3MF for `CaseS1_DualRF_BoltOn_v2.0` (`25 × 25 mm` 4-Bolt Square-Flange N-Type + `4×` Captive M3 Hex Nut Sockets + GPS SMA).
- [`Top_Antenna_Rail_Dual_SMA_Only_v2.0.3mf`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/3MF/Top_Antenna_Rail_Dual_SMA_Only_v2.0.3mf) — Standalone single-part 3MF for `CaseS1_DualRF_v2.0` (Dual-SMA: 915 MHz SMA + GPS SMA).
- [`Wio_Tracker_L1_Updated_Parts_v2.0.3mf`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/3MF/Wio_Tracker_L1_Updated_Parts_v2.0.3mf) — Single-plate 3MF containing only the updated Wio Tracker L1 parts + both top antenna rails.
- [`MeshSlide_WioTrackerL1_Kit_v2.0.3mf`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/3MF/MeshSlide_WioTrackerL1_Kit_v2.0.3mf) — Complete Seeed Wio Tracker L1 (OLED) enclosure kit.
- [`MeshSlide_RAK19007_Kit_v2.0.3mf`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/3MF/MeshSlide_RAK19007_Kit_v2.0.3mf) — Complete RAK19007 WisBlock enclosure kit.
- [`CardKB_Pro_Hybrid_Kit_v2.0.3mf`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/3MF/CardKB_Pro_Hybrid_Kit_v2.0.3mf) — CardKB Pro Hybrid keyboard kit.

### 2. Versioned Part Directories (`STL/` & `STEP/`)
- `STL/Wio_Tracker_L1_v2.0/` & `STEP/Wio_Tracker_L1_v2.0/` — Self-contained 9-part Wio Tracker L1 set (`*_v2.0.stl` / `*_v2.0.step`).
- `STL/RAK_WisBlock_v2.0/` & `STEP/RAK_WisBlock_v2.0/` — Self-contained 8-part RAK19007 WisBlock set (`*_v2.0.stl` / `*_v2.0.step`).
- `STL/CardKB_Pro_v2.0/` & `STEP/CardKB_Pro_v2.0/` — Self-contained 9-part CardKB Pro Hybrid set (`*_v2.0.stl` / `*_v2.0.step`).

### Key Changes in `v2.0`
- **Top Dual-RF Bulkhead Rails (`CaseS1_DualRF_v2.0` & `CaseS1_DualRF_BoltOn_v2.0`)**:
  - Eliminated overhanging rear-mount N-Type turret (`Ø23 mm` flange wider than `18 mm` case).
  - Shifted 915 MHz port (`X = 68.50 mm`) and GPS SMA port (`X = 48.50 mm`) left of the right-side M2 screw boss ear.
  - `CaseS1_DualRF_v2.0`: Flush `18.0 mm` Dual-SMA top rail (915 MHz SMA + GPS SMA) with unbroken `6.2 mm` deep 6-sided `8.25 mm` internal hex nut sockets (`Z = -4.40..+1.80 mm`) and flat `Z = +1.80 mm` underside ceiling.
  - `CaseS1_DualRF_BoltOn_v2.0`: Outside-Mount 4-Bolt Square-Flange N-Type (`27.4 × 26.8 mm` top flange pad at `Z = -7.20..-1.20 mm`, `18.30 × 18.30 mm` M3 bolt grid with `Ø3.40 mm` holes, `4×` captive `5.75 mm` AF M3 hex nut sockets, and `Ø10.60 mm` center bore) + GPS SMA.
- **Wio Tracker L1 Midframe & Bezel (`CaseM1_WioL1_v2.0` & `CaseU1_WioL1_v2.0`)**:
  - Full-depth left switch-side solder-pin relief trench (`X = 1.50..7.50 mm, Z = 12.50..52.50 mm`).
  - Full-depth rear SMD magnetic buzzer clearance window (`X = 39.0..51.5 mm, Z = 33.5..50.5 mm`).
  - Expanded bottom Grove keyboard plug & wire routing bay (`X = 5.0..75.0 mm, Z = 53.0..72.0 mm`).
  - Spliced MakerWorld Wio Tracker L1 OLED bezel, captive flex-frame pill Menu button (`CaseButton_WioL1_v2.0`), and conical-skirt Joystick cap (`CaseJoystick_v2.0`) with widened `X = 6.80..52.00 mm` internal button loop pocket.

---

## Archived Releases (`archive/`)
- [`archive/v1.0/`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/archive/v1.0) — Previous `v1.0` STL, STEP, and 3MF folders (`Wio_Tracker_L1/`, `RAK_WisBlock/`, `CardKB_Pro/`).
- [`archive/v0.9_legacy/`](file:///c:/Users/hanse/Documents/antigravity/splendid-bohr/archive/v0.9_legacy) — Initial flat STL/STEP exports and legacy subfolder layouts (`Common/`, `Complete_Build_*`, `Expansion_Modules/`).
