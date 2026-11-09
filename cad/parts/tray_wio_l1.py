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

    # 1. Outer PCB perimeter cradle (48.50 x 52.40 mm, X = 2.00..50.50, Z_M1 = 6.80..59.20, Y_M1 = 2.40..5.50)
    # The PCB rests at Y_M1 = 2.40 mm exclusively on the 4 corner M2 mounting pads (X = 2.0..7.3 & 45.2..50.5,
    # Z_M1 = 6.8..12.1 & 53.9..59.2), putting the PCB top at Y_M1 = 4.00 mm (Y_U1 = -1.20 mm, 8.00 mm below
    # the Y_U1 = 6.80 mm exterior front face, matching Wio-Tracker-L1-OLED.3mf!).
    # All four edges between the corner pads are cut completely through the backplane (Y_M1 = -0.5..5.5):
    #   - Center & Top/Bottom window (X = 7.30..45.20, Z_M1 = 6.80..59.20): clears top '100' inductor, GPS IPEX,
    #     LoRa shield, and bottom-left BAT JST socket.
    #   - Left Solder-Pin Through-Slot (X = 1.80..8.50, Z_M1 = 12.10..53.90): removes the inner bezel ledge
    #     behind the RST button, ON/OFF slide switch, and USB-C soldered through-hole pins.
    #   - Right Buzzer Through-Window (X = 40.00..52.50, Z_M1 = 12.10..53.90): removes the inner bezel ledge
    #     behind the rear SMD magnetic BUZZER (Z_M1 = 36.0..47.0 mm) and RF coax transition.
    x0 = WIO_PCB_X0
    x1 = x0 + WIO_PCB_L
    z0 = WIO_PCB_Z0
    z1 = z0 + WIO_PCB_W

    wio_outer_cradle = box_from_bounds(x0, x1, 2.40, 5.50, z0, z1)
    wio_center_window = box_from_bounds(7.30, 45.20, -0.50, 5.50, z0, z1)
    left_solder_pin_window = box_from_bounds(1.80, 8.50, -0.50, 5.50, 12.10, 53.90)
    right_buzzer_window = box_from_bounds(40.00, 52.50, -0.50, 5.50, 12.10, 53.90)

    # 2. Lower Grove I2C Plug & Wire Bend Bay (Z_M1 = 59.00..69.50 mm, 10.50 mm vertical clearance below PCB!)
    # The white 4-pin Grove socket on the bottom edge of the Wio PCB sits at X = 33.45..46.61, Z_M1 = 49.68..59.14.
    # When the mating white Grove plug is inserted, its housing + 4-wire bend extends 9-10 mm below Z_M1 = 59.00.
    grove_plug_entry = box_from_bounds(31.20, 47.00, 0.80, 5.50, 49.00, 69.50)
    grove_plug_through = box_from_bounds(31.80, 46.50, -0.50, 5.50, 50.00, 65.50)
    grove_wire_bay = box_from_bounds(15.00, 89.00, 1.00, 5.50, 59.20, 69.50)

    # 3. Right-Side RF Coax & Expansion Bay (X = 52.2..89.0, Z_M1 = 14.5..69.5, Y = 1.2..5.5)
    # and top coax drop chute (X = 49.5..78.5, Z_M1 = 0.0..16.0)
    rf_bay = box_from_bounds(52.20, 89.00, 1.20, 5.50, 14.50, 69.50)
    rf_top_chute = box_from_bounds(50.50, 78.50, 1.20, 5.50, 0.00, 16.00)
    rf_bridge = box_from_bounds(48.00, 53.50, 2.40, 5.50, 12.10, 53.90)

    # 4. Left-Side Official Port Cutouts on X = -0.5..5.5 (bridging into the left solder-pin window):
    # Aligned to PCB bottom at Y_M1 = 2.40 mm:
    # - Top-left RST button slot: ZC - 15.90 = 17.10 mm (Z_M1 = 14.20..20.00)
    # - Middle-left ON/OFF Power slide switch slot: ZC - 6.00 = 27.00 mm (Z_M1 = 23.00..31.00)
    # - Lower-left USB Type-C port opening: ZC + 7.80 = 40.80 mm (Z_M1 = 35.60..46.00)
    #   + outer USB-C cable overmold counterbore (X = -0.5..1.3, Y = 1.5..5.5, Z_M1 = 34.60..47.00)
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
            right_buzzer_window,
            grove_plug_entry,
            grove_plug_through,
            grove_wire_bay,
            rf_bay,
            rf_top_chute,
            rf_bridge,
            left_io_slot,
        ],
        engine="manifold",
    )
    carved = trimesh.boolean.difference([blank, cutouts], engine="manifold")

    # 5. Add 4x corner M2 mounting bosses flush with the Y_M1 = 2.40 mm PCB support plane (43.06 x 47.00 mm grid)
    xc = x0 + WIO_PCB_L / 2.0  # 26.25 mm
    zc = z0 + WIO_PCB_W / 2.0  # 33.00 mm
    standoffs = []
    holes = []
    for sx in [-1.0, 1.0]:
        for sz in [-1.0, 1.0]:
            hx = xc + sx * (WIO_HOLE_DX / 2.0)
            hz = zc + sz * (WIO_HOLE_DZ / 2.0)
            standoffs.append(cylinder_y(hx, hz, 0.00, 2.40, radius=2.35, sections=36))
            holes.append(cylinder_y(hx, hz, -0.50, 2.90, radius=0.90, sections=36))

    with_bosses = trimesh.boolean.union([carved] + standoffs, engine="manifold")
    res = trimesh.boolean.difference([with_bosses, trimesh.boolean.union(holes, engine="manifold")], engine="manifold")
    res.merge_vertices()
    return res


def build_case_u1_wio_l1() -> trimesh.Trimesh:
    blank = _prepare_stretched_u1_blank(height_expansion=WIO_HEIGHT_EXPANSION)

    # 1. Internal clearance cavity behind the front bezel (Y_U1 = -0.20..4.80 mm):
    # Clears the 1.3" OLED module, 24P E-Ink FPC connector, Menu button flex-frame (19.8 x 17.0 x 3.7 mm,
    # spanning X_U1 = 31.44..51.24, Z_U1 = 30.77..47.77), Joystick conical skirt (Ø9.6 x 4.8 mm),
    # bottom Solar JST-2P, and bottom Grove I2C 4P + wire bend bay!
    stack_clearance = box_from_bounds(6.20, 84.00, -0.20, 3.80, 4.80, 67.50)
    upper_and_bezel_recess = box_from_bounds(6.80, 52.00, -0.20, 4.80, 4.80, 48.50)
    bottom_connectors_recess = box_from_bounds(6.20, 49.00, -0.20, 4.80, 44.50, 67.50)
    grove_wire_bay_u1 = box_from_bounds(15.00, 84.00, -0.20, 4.60, 56.50, 67.50)

    # 2. Left-Wall Matching Cutouts in CaseU1_WioL1 aligned with CaseM1_WioL1 (since Z_U1 = Z_M1 - 2.0):
    # - Top-left RST button slot (Z_U1 = 12.20..18.00, Y_U1 = -0.5..2.50)
    # - Middle Power slide switch slot (Z_U1 = 21.00..29.00, Y_U1 = -0.5..2.70)
    # - Lower-left USB-C port opening (Z_U1 = 33.60..44.00, Y_U1 = -0.5..3.30)
    #   + outer USB-C cable overmold counterbore (X = -0.5..1.3, Y_U1 = -0.5..4.00, Z_U1 = 32.60..45.00)
    u1_rst_slot = box_from_bounds(-0.50, 3.40, -0.50, 2.50, 12.20, 18.00)
    u1_pwr_slot = box_from_bounds(-0.50, 3.40, -0.50, 2.70, 21.00, 29.00)
    u1_usbc_slot = box_from_bounds(-0.50, 4.40, -0.50, 3.30, 33.60, 44.00)
    u1_usbc_overmold = box_from_bounds(-0.50, 1.30, -0.50, 4.00, 32.60, 45.00)

    # 3. Graft the exact MakerWorld Wio-Tracker-L1-OLED.3mf Front Bezel Patch (Wio_MW_Bezel_Patch.stl)
    # directly into CaseU1_WioL1 across X_U1 in [9.00, 51.00], Z_U1 in [5.00, 48.00]!
    # This grafts 100% of the proven MakerWorld front bezel:
    #   - Rounded-corner beveled 1.3" OLED window + 0.80 mm stepped glass retention lip
    #   - Beveled stadium/pill Menu button opening + underside half-round alignment peg & right guide tabs
    #   - Beveled conical 4-way Joystick opening (Ø8.00 -> Ø11.00 mm)
    patch_window_cut = box_from_bounds(9.00, 51.00, 3.50, 7.20, 5.00, 48.00)

    cutouts = trimesh.boolean.union(
        [
            stack_clearance,
            upper_and_bezel_recess,
            bottom_connectors_recess,
            grove_wire_bay_u1,
            u1_rst_slot,
            u1_pwr_slot,
            u1_usbc_slot,
            u1_usbc_overmold,
            patch_window_cut,
        ],
        engine="manifold",
    )
    carved_u1 = trimesh.boolean.difference([blank, cutouts], engine="manifold")

    mw_patch = trimesh.load(os.path.join(REF_STL_DIR, "Wio_MW_Bezel_Patch.stl"))
    patch_clip = box_from_bounds(8.80, 51.20, 3.50, 6.80, 4.80, 48.20)
    mw_patch_trimmed = trimesh.boolean.intersection([mw_patch, patch_clip], engine="manifold")

    res = trimesh.boolean.union([carved_u1, mw_patch_trimmed], engine="manifold")
    res.merge_vertices()
    return res


def build_case_joystick_wio_l1() -> trimesh.Trimesh:
    """
    Load the exact Joystick Cap from MakerWorld Wio-Tracker-L1-OLED.3mf (9.60 x 9.59 x 4.80 mm),
    oriented flat on Z=0 for support-free printing.
    """
    cap = trimesh.load(os.path.join(REF_STL_DIR, "Wio_MW_Joystick_Cap.stl"))
    bmin = cap.bounds[0]
    cap.apply_translation([-bmin[0], -bmin[1], -bmin[2]])
    return cap


def build_case_button_wio_l1() -> trimesh.Trimesh:
    """
    Load the exact captive flex-frame Menu Button from MakerWorld Wio-Tracker-L1-OLED.3mf
    (19.80 x 17.00 x 3.70 mm), oriented flat on Z=0 for support-free printing.
    """
    btn = trimesh.load(os.path.join(REF_STL_DIR, "Wio_MW_Menu_Button.stl"))
    bmin = btn.bounds[0]
    btn.apply_translation([-bmin[0], -bmin[1], -bmin[2]])
    return btn
