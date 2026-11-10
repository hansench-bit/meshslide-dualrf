"""
Generator for Pairing A: RAK WisBlock (RAK19007 + RAK4631 + RAK12500 + 0.96" I2C OLED).
Produces:
- CaseM1_RAK: +10mm expanded internal carrier frame (96.5 x 5.2 x 47.0 mm) with 60x30mm
  RAK19007 cradle, 4x M2 mounting standoffs, USB-C cutout, Rokland PID 920452 switch pocket,
  4-pin Grove I2C pogo routing channel, and top coax chute to CaseS1_DualRF.
- CaseU1_RAK: +10mm expanded front faceplate (96.5 x 6.8 x 45.0 mm) with beveled 0.96" OLED
  viewing window, 4x OLED module support ledges, and Reset button actuator hole.
- CaseButton_RAK: Tactile Reset button actuator cap.
"""

from __future__ import annotations
import os
import numpy as np
import trimesh
from cad.config import (
    REF_STL_DIR,
    HEIGHT_EXPANSION,
    STRETCH_SPLIT_Z_M1,
    STRETCH_SPLIT_Z_L1,
    RAK_PCB_L,
    RAK_PCB_W,
    RAK_PCB_X0,
    RAK_PCB_Z0,
    RAK_HOLE_DX,
    RAK_HOLE_DZ,
    RAK_OLED_WIN_W,
    RAK_OLED_WIN_H,
    RAK_OLED_PCB_W,
    RAK_OLED_PCB_H,
    RAK_OLED_CENTER_X,
    RAK_OLED_CENTER_Z,
    ROKLAND_SW_Z_CENTER,
    ROKLAND_SW_BODY_L,
    ROKLAND_SW_BODY_W,
    ROKLAND_SW_BODY_D,
    ROKLAND_SW_SLOT_L,
    ROKLAND_SW_SLOT_W,
    box_from_bounds,
    cylinder_y,
    chamfered_window_y,
    stretch_mesh_z,
)


def _prepare_stretched_m1_blank(height_expansion: float = HEIGHT_EXPANSION) -> trimesh.Trimesh:
    """
    Create a clean stretched CaseM1 structural frame (+10mm for RAK, +28mm for Wio L1) that preserves:
    - Top tongue (X=21.1..48.0, Z=0..2.0) and top M2x4 screw boss (X=10.5, Z=0..8.0)
    - Right-hand step profile for CaseS1 (X=77.5..96.5, Z=2..21)
    - Bottom CaseR1 perimeter step, 2x M2x5 brass nut bosses (X=30.25, 66.25),
      2x CaseSlide dovetail sockets (X=13..21.5, 75..83.5),
      CaseSlide M2x5 lock screw hole (X=86.75), and 8-pin pogo slot (X=36..60.5).
    """
    orig_m1 = trimesh.load(os.path.join(REF_STL_DIR, "CaseM1.STL"))
    stretched = stretch_mesh_z(orig_m1, split_z=STRETCH_SPLIT_Z_M1, delta_z=height_expansion)

    # Fill the old Heltec V4 / L76K interior zone with a clean solid web (Y=0..5.2)
    # while staying clear of the top M2 screw (X=10.5, Z=0..7.5) and bottom dovetails/brass nuts (Z >= 30.2 + height_expansion)
    z_bot_fill = 30.2 + height_expansion
    fill_left = box_from_bounds(0.0, 77.5, 0.0, 5.2, 8.0, z_bot_fill)
    fill_right = box_from_bounds(77.5, 90.5, 0.0, 5.2, 14.5, z_bot_fill)
    fill_far_right = box_from_bounds(90.5, 96.5, 0.0, 5.2, 22.0, z_bot_fill)
    body = trimesh.boolean.union([stretched, fill_left, fill_right, fill_far_right], engine="manifold")

    # Trim the right portion of the top white tongue (X=42.5..78.5, Z=0..6.5) so the shifted SMA (X=48.5)
    # + N-Type (X=68.5) coax pigtails from CaseS1_DualRF drop straight into the CaseM1 RF bay!
    coax_top_opening = box_from_bounds(42.5, 78.5, -0.5, 5.7, -0.5, 6.5)
    coax_front_chute_left = box_from_bounds(42.5, 50.5, 2.0, 5.7, 6.0, 15.5)
    coax_front_chute_right = box_from_bounds(50.5, 78.5, 1.2, 5.7, 6.0, 15.5)

    # Re-clear the 8-pin pogo solder access window at the bottom center (X=36.0..60.5, Z=28.0+ext..35.0+ext)
    pogo_wire_bay = box_from_bounds(36.0, 60.5, 1.0, 5.5, 28.0 + height_expansion, 35.0 + height_expansion)

    return trimesh.boolean.difference(
        [body, trimesh.boolean.union([coax_top_opening, coax_front_chute_left, coax_front_chute_right, pogo_wire_bay], engine="manifold")],
        engine="manifold",
    )


def build_case_m1_rak() -> trimesh.Trimesh:
    blank = _prepare_stretched_m1_blank()

    # 1. Carve the 60.4 x 30.4 mm RAK19007 PCB cradle (X = 2.0..62.4, Z = 6.5..36.9, Y = 1.2..5.5)
    x0 = RAK_PCB_X0
    x1 = x0 + RAK_PCB_L
    z0 = RAK_PCB_Z0
    z1 = z0 + RAK_PCB_W
    rak_pocket = box_from_bounds(x0, x1, 1.2, 5.5, z0, z1)

    # 2. Carve battery & Grove I2C wire pass-through window in the 1.2mm backplane (X = 22.0..56.0, Z = 12.0..34.0)
    backplane_window = box_from_bounds(22.0, 56.0, -0.5, 2.0, 12.0, 34.0)

    # 3. Carve Right-Side RF Coax & Sensor Bay (X = 63.8..89.0, Z = 14.5..39.0, Y = 1.2..5.5)
    # connected to the top coax chute (X = 50.0..77.5, Z = 0.0..16.0)
    rf_bay = box_from_bounds(63.8, 89.0, 1.2, 5.5, 14.5, 39.0)
    rf_top_chute = box_from_bounds(50.0, 77.6, 1.2, 5.5, 0.0, 16.0)
    # Wire bridge between RAK19007 right edge and RF bay for LoRa & GPS IPEX pigtails
    rf_bridge = box_from_bounds(60.0, 65.0, 1.8, 5.5, 9.0, 35.0)

    # 4. Left-Side USB-C Connector Cutout (X = -0.5..5.5, Y = 1.6..5.5, Z = 16.5..26.5)
    # Plus outer cable plug overmold counterbore (X = -0.5..1.3, Y = 1.2..5.5, Z = 15.5..27.5)
    usbc_cutout = box_from_bounds(-0.5, 5.5, 1.6, 5.5, 16.5, 26.5)
    usbc_overmold_m1 = box_from_bounds(-0.5, 1.3, 1.2, 5.5, 15.5, 27.5)

    # 5. Left-Side Rokland PID 920452 Inline Slide Switch Pocket (centered at Z = 33.5, straddling Y = 0)
    sw_pocket = box_from_bounds(
        1.2, 1.2 + ROKLAND_SW_BODY_D,
        -0.5, 1.6,
        ROKLAND_SW_Z_CENTER - ROKLAND_SW_BODY_L / 2.0, ROKLAND_SW_Z_CENTER + ROKLAND_SW_BODY_L / 2.0,
    )
    sw_slot = box_from_bounds(
        -0.5, 2.5,
        -0.5, 1.2,
        ROKLAND_SW_Z_CENTER - ROKLAND_SW_SLOT_L / 2.0, ROKLAND_SW_Z_CENTER + ROKLAND_SW_SLOT_L / 2.0,
    )

    cutouts = trimesh.boolean.union(
        [rak_pocket, backplane_window, rf_bay, rf_top_chute, rf_bridge, usbc_cutout, usbc_overmold_m1, sw_pocket, sw_slot],
        engine="manifold",
    )
    carved = trimesh.boolean.difference([blank, cutouts], engine="manifold")

    # 6. Add 4x M2 Mounting Standoffs for RAK19007 (at corners of 55.2 x 25.2 mm pattern)
    xc = x0 + RAK_PCB_L / 2.0
    zc = z0 + RAK_PCB_W / 2.0
    standoffs = []
    holes = []
    for sx in [-1.0, 1.0]:
        for sz in [-1.0, 1.0]:
            hx = xc + sx * (RAK_HOLE_DX / 2.0)
            hz = zc + sz * (RAK_HOLE_DZ / 2.0)
            standoffs.append(cylinder_y(hx, hz, 1.0, 2.6, radius=2.3, sections=36))
            holes.append(cylinder_y(hx, hz, 0.4, 3.2, radius=0.92, sections=36))

    with_bosses = trimesh.boolean.union([carved] + standoffs, engine="manifold")
    return trimesh.boolean.difference([with_bosses, trimesh.boolean.union(holes, engine="manifold")], engine="manifold")


def _prepare_stretched_u1_blank(height_expansion: float = HEIGHT_EXPANSION) -> trimesh.Trimesh:
    """
    Transform original CaseU1.STL into unified assembly orientation:
      X in [0, 96.5] (Left=0, Right=96.5)
      Y in [0, 6.8]  (Interior mating face=0.0, Exterior front face=6.8)
      Z in [0, 35.0 + height_expansion] (Top=0.0, Bottom=35.0+ext, where Z_assy = Z_U1 + 2.0)
    Stretch by +height_expansion at Z_U1 = 22.0mm and seal the old Heltec V4 screen & button holes
    while preserving 100% of the top/bottom M2 mounting holes, perimeter steps, and //\\ logo!
    """
    u1_raw = trimesh.load(os.path.join(REF_STL_DIR, "CaseU1.STL"))
    # Map (x_raw, y_raw, z_raw) -> (96.5 - z_raw, y_raw, x_raw)
    T = np.array([
        [0, 0, -1, 96.5],
        [0, 1, 0, 0.0],
        [1, 0, 0, 0.0],
        [0, 0, 0, 1.0],
    ])
    u1_oriented = u1_raw.copy().apply_transform(T)

    # Extract the original crisp //\ logo negative relief from u1_oriented (X=56..86, Y=5.8..7.0, Z=13.5..28.5)
    logo_zone = box_from_bounds(56.0, 86.0, 5.8, 6.8, 13.5, 28.5)
    orig_logo_groove = trimesh.boolean.difference([logo_zone, u1_oriented], engine="manifold")
    # Shift the crisp original logo down so it sits centered on the expanded faceplate (8.0mm for +10mm, 17.0mm for +28mm)
    logo_shift_z = 8.0 + 0.5 * (height_expansion - 10.0)
    orig_logo_groove.apply_translation([0.0, 0.0, logo_shift_z])

    # Plane the front face before stretching so the stretch does not distort the diagonal //\ grooves
    pre_seal_logo = box_from_bounds(55.5, 86.5, 5.4, 6.8, 13.5, 28.5)
    u1_clean = trimesh.boolean.union([u1_oriented, pre_seal_logo], engine="manifold")

    stretched = stretch_mesh_z(u1_clean, split_z=STRETCH_SPLIT_Z_L1, delta_z=height_expansion)

    # Seal old Heltec V4 screen cutout, left button cutouts, and old left-wall Heltec USB-C notch (Z_U1=11.05..20.55)
    # Staying strictly within Z_U1 = [4.2, 28.0 + height_expansion] so top CaseS1 step and bottom CaseR1 step remain untouched!
    z_bot_seal = 28.0 + height_expansion
    seal_front = box_from_bounds(2.2, 60.0, 2.6, 6.8, 4.2, z_bot_seal)
    seal_left_wall = box_from_bounds(0.0, 3.5, 0.0, 6.2, 6.0, z_bot_seal)
    solid_front = trimesh.boolean.union([stretched, seal_front, seal_left_wall], engine="manifold")
    return trimesh.boolean.difference([solid_front, orig_logo_groove], engine="manifold")


def build_case_u1_rak() -> trimesh.Trimesh:
    blank = _prepare_stretched_u1_blank()

    # 1. Carve beveled 0.96" OLED viewing window (25.0 x 14.5 mm centered at X=35.0, Z_U1=19.5)
    z_u1_oled = RAK_OLED_CENTER_Z - 2.0  # 19.5 mm in U1 coords
    oled_window = chamfered_window_y(
        RAK_OLED_CENTER_X, z_u1_oled, RAK_OLED_WIN_W, RAK_OLED_WIN_H, ymin=2.0, ymax=6.8, bevel=1.3
    )

    # 2. Carve internal recess for 0.96" OLED PCB (28.4 x 28.0 mm, Y = 0.0 to 4.8) with corner support ledges
    oled_pcb_recess = box_from_bounds(
        RAK_OLED_CENTER_X - RAK_OLED_PCB_W / 2.0,
        RAK_OLED_CENTER_X + RAK_OLED_PCB_W / 2.0,
        -0.2, 4.8,
        z_u1_oled - RAK_OLED_PCB_H / 2.0,
        z_u1_oled + RAK_OLED_PCB_H / 2.0,
    )
    # Clear internal space behind front wall for RAK4631 / RAK12500 stack (X = 3.5..84.0, Y = -0.2..3.6, Z = 4.5..36.5)
    stack_clearance = box_from_bounds(3.5, 84.0, -0.2, 3.6, 4.5, 36.5)

    # 3. Reset button actuator cutout on the left side (X = 6.5, Z_U1 = 10.5) matching CaseButton (5.0 x 7.0 mm flange, 2.9 x 4.9 mm cap)
    btn_xc, btn_zc = 6.5, 10.5
    btn_hole = box_from_bounds(btn_xc - 2.6, btn_xc + 2.6, -0.5, 7.2, btn_zc - 1.6, btn_zc + 1.6)
    btn_flange_recess = box_from_bounds(btn_xc - 3.7, btn_xc + 3.7, -0.5, 4.2, btn_zc - 2.7, btn_zc + 2.7)

    # 4. Left-Wall USB-C Cutout + Cable Overmold Recess matching CaseM1_RAK (Z_M1 = 16.5..26.5 -> Z_U1 = 14.5..24.5)
    usbc_u1_slot = box_from_bounds(-0.5, 4.0, -0.5, 2.8, 14.5, 24.5)
    usbc_u1_overmold = box_from_bounds(-0.5, 1.3, -0.5, 3.5, 13.5, 25.5)

    cutouts = trimesh.boolean.union(
        [oled_window, oled_pcb_recess, stack_clearance, btn_hole, btn_flange_recess, usbc_u1_slot, usbc_u1_overmold],
        engine="manifold",
    )
    return trimesh.boolean.difference([blank, cutouts], engine="manifold")


def build_case_button() -> trimesh.Trimesh:
    """Return the tactile button actuator cap (CaseButton)."""
    return trimesh.load(os.path.join(REF_STL_DIR, "CaseButton.STL"))
