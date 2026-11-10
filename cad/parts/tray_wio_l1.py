"""
Generator for Pairing B: Seeed Studio Wio Tracker L1 (Official 48.06 x 52.00 mm PCB Layout).
Uses the exact proven front bezel, captive flex-frame pill Menu button, and conical-skirt Joystick cap
extracted directly from the MakerWorld Wio Tracker L1 OLED 3000mAh enclosure (Wio-Tracker-L1-OLED.3mf,
https://makerworld.com/en/models/2332112-wio-tracker-l1-oled-case-3000mah):
- Bare PCB: 48.06 mm wide (X) x 52.00 mm tall (Z), 4x corner M2 holes on a 43.06 x 47.00 mm grid
- PCB rests on 4-corner-only M2 standoffs at Y_M1 = 2.40 mm (PCB top at Y_M1 = 4.00 mm / Y_U1 = -1.20 mm,
  giving the exact 8.00 mm PCB-top-to-front-face and 6.00 mm PCB-top-to-inner-bezel-ceiling stackup!)
- Full through-backplane clearances on left edge (switch/USB-C soldered pins), right edge (rear Buzzer),
  top edge (100 inductor & GPS IPEX), and bottom edge (BAT JST & Grove I2C socket)
- +10.5 mm lower Grove Plug & Wire Bend Bay (Z_M1 = 59.0..69.5 mm) below the PCB so the white 4-pin
  Grove connector + wire loop plug directly into the bottom of the Wio PCB without hitting the frame
"""

from __future__ import annotations
import os
import trimesh
from cad.config import (
    REF_STL_DIR,
    WIO_HEIGHT_EXPANSION,
    WIO_PCB_L,
    WIO_PCB_W,
    WIO_PCB_X0,
    WIO_PCB_Z0,
    WIO_HOLE_DX,
    WIO_HOLE_DZ,
    box_from_bounds,
    cylinder_y,
)
from cad.parts.tray_rak19007 import _prepare_stretched_m1_blank, _prepare_stretched_u1_blank


def build_case_m1_wio_l1() -> trimesh.Trimesh:
    blank = _prepare_stretched_m1_blank(height_expansion=WIO_HEIGHT_EXPANSION)

    # Reinforce the top-right frame bridge around Boss #1 (X = 47.78, Z_M1 = 9.50) before carving
    top_right_boss_bridge = box_from_bounds(39.00, 53.50, 0.00, 2.40, 2.20, 13.00)
    blank = trimesh.boolean.union([blank, top_right_boss_bridge], engine="manifold")

    x0 = WIO_PCB_X0
    x1 = x0 + WIO_PCB_L
    z0 = WIO_PCB_Z0
    z1 = z0 + WIO_PCB_W

    wio_outer_cradle = box_from_bounds(x0, x1, 2.40, 5.50, z0, z1)
    # Leave larger 8.0 x 8.0 mm solid corner webs around all 4 M2 bosses (especially top-right Boss #1)
    wio_center_window = box_from_bounds(8.00, 44.50, -0.50, 5.50, z0, z1)
    left_solder_pin_window = box_from_bounds(1.80, 8.50, -0.50, 5.50, 12.80, 53.20)

    # 2. Full Bottom Battery Plug (#2) + Grove I2C Plug & Wire Bend Bay (X = 7.50..46.80, Z_M1 = 49.00..69.50)
    # Cuts completely through the backplane (Y_M1 = -0.50..5.50) across both the bottom-left BAT JST socket (#2)
    # and the bottom-right Grove I2C socket so the battery plug and Grove plug both have full clearance!
    bottom_plugs_through = box_from_bounds(7.50, 46.80, -0.50, 5.50, 49.00, 69.50)
    grove_wire_bay = box_from_bounds(7.50, 89.00, 0.80, 5.50, 59.20, 69.50)

    # 3. Right-Side Antenna Cord & Connector Passage (#3: X = 44.50..88.00, Z_M1 = 12.80..68.00)
    # Cuts completely through the right side of the PCB (X = 44.50..85.00, Z_M1 = 12.80..53.20, Y_M1 = -0.50..5.50)
    # and opens the top coax drop chute (X = 52.00..85.00, Z_M1 = 0.00..16.00) so the antenna cord passes freely!
    right_coax_through = box_from_bounds(44.50, 85.00, -0.50, 5.50, 12.80, 53.20)
    rf_bay = box_from_bounds(51.50, 89.00, 0.80, 5.50, 12.80, 69.50)
    rf_top_chute = box_from_bounds(52.00, 85.00, 0.80, 5.50, -0.50, 16.00)
    rf_top_slot_through = box_from_bounds(53.00, 82.00, -0.50, 5.50, 2.00, 16.00)

    # 4. Left-Side Official Port Cutouts on X = -0.5..5.5:
    rst_slot = box_from_bounds(-0.50, 5.50, 2.10, 5.50, 14.20, 20.00)
    pwr_sw_slot = box_from_bounds(-0.50, 5.50, 2.10, 5.50, 23.00, 31.00)
    usbc_slot = box_from_bounds(-0.50, 5.50, 1.90, 5.50, 35.60, 46.00)
    usbc_overmold_m1 = box_from_bounds(-0.50, 1.30, 1.50, 5.50, 34.60, 47.00)
    left_io_slot = trimesh.boolean.union(
        [rst_slot, pwr_sw_slot, usbc_slot, usbc_overmold_m1], engine="manifold"
    )

    cutouts = trimesh.boolean.union(
        [
            wio_outer_cradle,
            wio_center_window,
            left_solder_pin_window,
            bottom_plugs_through,
            grove_wire_bay,
            right_coax_through,
            rf_bay,
            rf_top_chute,
            rf_top_slot_through,
            left_io_slot,
        ],
        engine="manifold",
    )
    carved = trimesh.boolean.difference([blank, cutouts], engine="manifold")

    # 5. Add reinforced 4x corner M2 mounting bosses (radius = 3.10 mm + corner gusset blocks) flush with Y_M1 = 2.40 mm
    xc = x0 + WIO_PCB_L / 2.0  # 26.25 mm
    zc = z0 + WIO_PCB_W / 2.0  # 33.00 mm
    standoffs = [
        # Extra solid gusset around top-right Boss #1 (hx=47.78, hz=9.50) anchoring it to the top/right frame
        box_from_bounds(43.80, 52.00, 0.00, 2.40, 4.00, 12.80),
        # Extra solid gusset around top-left Boss (hx=4.72, hz=9.50)
        box_from_bounds(2.00, 8.20, 0.00, 2.40, 5.50, 12.80),
        # Extra solid gusset around bottom-left Boss (hx=4.72, hz=56.50)
        box_from_bounds(2.00, 8.00, 0.00, 2.40, 53.20, 59.50),
        # Extra solid gusset around bottom-right Boss (hx=47.78, hz=56.50), clear of Grove plug at X<=46.8, Z>=59.0
        box_from_bounds(46.85, 51.50, 0.00, 2.40, 53.20, 59.00),
    ]
    holes = []
    for sx in [-1.0, 1.0]:
        for sz in [-1.0, 1.0]:
            hx = xc + sx * (WIO_HOLE_DX / 2.0)
            hz = zc + sz * (WIO_HOLE_DZ / 2.0)
            boss_r = 3.30 if (sx > 0 and sz < 0) else 2.45
            standoffs.append(cylinder_y(hx, hz, 0.00, 2.40, radius=boss_r, sections=36))
            holes.append(cylinder_y(hx, hz, -0.50, 2.90, radius=0.90, sections=36))

    with_bosses = trimesh.boolean.union([carved] + standoffs, engine="manifold")
    res = trimesh.boolean.difference([with_bosses, trimesh.boolean.union(holes, engine="manifold")], engine="manifold")
    res.merge_vertices()
    return res


def build_case_u1_wio_l1() -> trimesh.Trimesh:
    blank = _prepare_stretched_u1_blank(height_expansion=WIO_HEIGHT_EXPANSION)

    # 1. Internal clearance cavity behind the front bezel (Y_U1 = -0.20..4.80 mm):
    # Thins the left outer wall all the way back to X = 2.00 mm (matching the MakerWorld reference's 2.03 mm
    # left wall and eliminating the old 6.80/6.20 mm inner step and Z=44.5 mm notch) so the Wio Tracker L1
    # board (X = 2.22..50.28 mm) sits 100% flush against the faceplate!
    stack_clearance = box_from_bounds(2.00, 84.00, -0.20, 3.80, 4.80, 67.50)
    upper_oled_recess = box_from_bounds(2.00, 52.00, -0.20, 4.80, 4.80, 30.00)
    left_mid_recess = box_from_bounds(2.00, 30.50, -0.20, 4.80, 30.00, 48.50)
    bottom_connectors_recess = box_from_bounds(2.00, 52.00, -0.20, 4.80, 46.20, 67.50)
    grove_wire_bay_u1 = box_from_bounds(7.50, 84.00, -0.20, 4.60, 56.50, 67.50)

    # 2. Left-Wall Matching Cutouts in CaseU1_WioL1 aligned with CaseM1_WioL1 (since Z_U1 = Z_M1 - 2.0):
    u1_rst_slot = box_from_bounds(-0.50, 3.40, -0.50, 2.50, 12.20, 18.00)
    u1_pwr_slot = box_from_bounds(-0.50, 3.40, -0.50, 2.70, 21.00, 29.00)
    u1_usbc_slot = box_from_bounds(-0.50, 4.40, -0.50, 3.30, 33.60, 44.00)
    u1_usbc_overmold = box_from_bounds(-0.50, 1.30, -0.50, 4.00, 32.60, 45.00)

    # 3. Graft the complete MakerWorld Wio-Tracker-L1-OLED.3mf Front Bezel + Full-Depth Menu Button Snap
    # Retention Hooks (Y_U1 = 3.00..6.80 mm), Half-Round Alignment Peg (Y_U1 = 2.00..6.80 mm), and Right
    # Button Guide Wall (X_U1 = 51.24..53.20 mm, Y_U1 = 1.40..6.80 mm)!
    patch_window_cut = box_from_bounds(9.00, 53.00, 3.50, 7.20, 5.00, 48.00)
    patch_btn_bay_cut = box_from_bounds(30.50, 53.20, -0.20, 7.20, 30.00, 46.20)

    cutouts = trimesh.boolean.union(
        [
            stack_clearance,
            upper_oled_recess,
            left_mid_recess,
            bottom_connectors_recess,
            grove_wire_bay_u1,
            u1_rst_slot,
            u1_pwr_slot,
            u1_usbc_slot,
            u1_usbc_overmold,
            patch_window_cut,
            patch_btn_bay_cut,
        ],
        engine="manifold",
    )
    carved_u1 = trimesh.boolean.difference([blank, cutouts], engine="manifold")

    mw_patch = trimesh.load(os.path.join(REF_STL_DIR, "Wio_MW_Bezel_Patch.stl"))
    res = trimesh.boolean.union([carved_u1, mw_patch], engine="manifold")
    res.merge_vertices()
    return res


def build_case_joystick_wio_l1() -> trimesh.Trimesh:
    """
    Load the Joystick Cap from MakerWorld Wio-Tracker-L1-OLED.3mf (9.60 x 9.59 x 4.80 mm)
    and tighten the underside square stem hole by a hair (from 2.10 x 2.10 mm down to 1.92 x 1.92 mm,
    i.e. +0.09 mm inward per wall) so it grips the Wio 5-way joystick post snugly without wobble.
    """
    cap = trimesh.load(os.path.join(REF_STL_DIR, "Wio_MW_Joystick_Cap.stl"))
    bmin = cap.bounds[0]
    cap.apply_translation([-bmin[0], -bmin[1], -bmin[2]])

    cx, cy = 4.8000, 4.7930
    # Fill the original 2.10 x 2.10 mm square socket (Z = 0.00..2.40 mm) and re-cut at 1.92 x 1.92 mm
    fill_old_sq = box_from_bounds(cx - 1.20, cx + 1.20, cy - 1.20, cy + 1.20, 0.00, 2.40)
    half_sq = 1.92 / 2.0  # 0.96 mm (tightened by 0.09 mm per side from 1.05 mm)
    new_sq_hole = box_from_bounds(cx - half_sq, cx + half_sq, cy - half_sq, cy + half_sq, -0.20, 2.45)

    solid_cap = trimesh.boolean.union([cap, fill_old_sq], engine="manifold")
    tight_cap = trimesh.boolean.difference([solid_cap, new_sq_hole], engine="manifold")
    tight_cap.merge_vertices()
    return tight_cap


def build_case_button_wio_l1() -> trimesh.Trimesh:
    """
    Load the exact captive flex-frame Menu Button from MakerWorld Wio-Tracker-L1-OLED.3mf
    (19.80 x 17.00 x 3.70 mm), oriented flat on Z=0 for support-free printing.
    """
    btn = trimesh.load(os.path.join(REF_STL_DIR, "Wio_MW_Menu_Button.stl"))
    bmin = btn.bounds[0]
    btn.apply_translation([-bmin[0], -bmin[1], -bmin[2]])
    return btn
