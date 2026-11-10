"""
Generator for CaseL1_Deep (Expanded +10mm Height & +4mm Deep Rear Battery Cover)
and CaseR1 (Bottom Perimeter Collar Ring) + CaseSlide (Bottom 8-Pin Pogo Rail).
"""

from __future__ import annotations
import os
import numpy as np
import trimesh
from cad.config import (
    REF_STL_DIR,
    HEIGHT_EXPANSION,
    WIO_HEIGHT_EXPANSION,
    STRETCH_SPLIT_Z_L1,
    BATTERY_EXTRA_DEPTH,
    ROKLAND_SW_Z_CENTER,
    ROKLAND_SW_BODY_L,
    ROKLAND_SW_BODY_W,
    ROKLAND_SW_BODY_D,
    ROKLAND_SW_SLOT_L,
    ROKLAND_SW_SLOT_W,
    box_from_bounds,
    stretch_mesh_z,
)


def build_case_l1_deep(with_rokland_switch: bool = True, height_expansion: float | None = None) -> trimesh.Trimesh:
    if height_expansion is None:
        height_expansion = HEIGHT_EXPANSION if with_rokland_switch else WIO_HEIGHT_EXPANSION

    orig_l1 = trimesh.load(os.path.join(REF_STL_DIR, "CaseL1.STL"))

    # 1. Stretch vertically by +height_expansion at Z_L1 = 22.0mm (preserving top CaseS1 & bottom CaseR1 interfaces)
    stretched_l1 = stretch_mesh_z(orig_l1, split_z=STRETCH_SPLIT_Z_L1, delta_z=height_expansion)

    # 2. Add +6.6mm outward rear battery shell expansion (Y = -6.6 to +2.0)
    x0, x1 = 0.0, 85.95
    y_in = 2.0
    y_base = 0.0
    y_ext = -BATTERY_EXTRA_DEPTH  # -6.6 mm
    z_top_0, z_top_1 = 3.2, 6.2
    z_bot_1, z_bot_0 = 25.6 + height_expansion, 28.6 + height_expansion

    verts_outer = np.array([
        # Base rectangle at Y = y_in (inside existing wall)
        [x0, y_in, z_top_0], [x1, y_in, z_top_0], [x1, y_in, z_bot_0], [x0, y_in, z_bot_0],
        # Base rectangle at Y = 0.0
        [x0, y_base, z_top_0], [x1, y_base, z_top_0], [x1, y_base, z_bot_0], [x0, y_base, z_bot_0],
        # Extended back plate at Y = -6.6 (chamfered in Z and right X edge)
        [x0, y_ext, z_top_1], [x1 - 2.0, y_ext, z_top_1], [x1 - 2.0, y_ext, z_bot_1], [x0, y_ext, z_bot_1],
    ], dtype=float)
    outer_bump = trimesh.convex.convex_hull(verts_outer)

    body = trimesh.boolean.union([stretched_l1, outer_bump], engine="manifold")

    # 3. Carve expanded internal battery bay (11.0 mm clear internal depth: Y = -5.0 to +6.0 mm!)
    # Leaves a 1.6mm solid rear wall (Y = -6.6 to -5.0) and 2.0mm perimeter walls
    xi0, xi1 = 2.0, 84.0
    yi_floor = -BATTERY_EXTRA_DEPTH + 1.6  # -5.0 mm (11.0 mm clear depth to Y=+6.0 mm!)
    yi_open = 6.2
    zi_top_0, zi_top_1 = 4.2, 6.6
    zi_bot_1, zi_bot_0 = 25.2 + height_expansion, 28.4 + height_expansion

    verts_cavity = np.array([
        [xi0, 1.0, zi_top_0], [xi1, 1.0, zi_top_0], [xi1, 1.0, zi_bot_0], [xi0, 1.0, zi_bot_0],
        [xi0, yi_open, zi_top_0], [xi1, yi_open, zi_top_0], [xi1, yi_open, zi_bot_0], [xi0, yi_open, zi_bot_0],
        [xi0, yi_floor, zi_top_1], [xi1 - 1.5, yi_floor, zi_top_1], [xi1 - 1.5, yi_floor, zi_bot_1], [xi0, yi_floor, zi_bot_1],
    ], dtype=float)
    battery_cavity = trimesh.convex.convex_hull(verts_cavity)

    if not with_rokland_switch:
        # Wio Tracker L1 uses its own onboard power slide switch above the USB-C port,
        # so the rear battery cover has a clean, solid left wall with no extra switch hole.
        return trimesh.boolean.difference([body, battery_cavity], engine="manifold")

    # 4. Carve the Captive Inline Slide Switch Pocket for Rokland PID 920452 (on left wall X=0, used on RAK19007)
    # In L1 coords, Z_L1 = ROKLAND_SW_Z_CENTER - 2.0 = 31.5 mm
    sw_zc = ROKLAND_SW_Z_CENTER - 2.0
    # Internal body pocket straddling the L1/M1 seam (Y = 2.5 to 6.5, X = 1.2 to 5.8, Z = sw_zc +/- 4.5)
    sw_body_pocket = box_from_bounds(
        1.2, 1.2 + ROKLAND_SW_BODY_D,
        6.0 - ROKLAND_SW_BODY_W + 0.8, 6.5,
        sw_zc - ROKLAND_SW_BODY_L / 2.0, sw_zc + ROKLAND_SW_BODY_L / 2.0,
    )
    # External actuator slider slot on left edge (X = -0.5 to 2.0)
    sw_actuator_slot = box_from_bounds(
        -0.5, 2.5,
        6.0 - ROKLAND_SW_SLOT_W + 0.4, 6.5,
        sw_zc - ROKLAND_SW_SLOT_L / 2.0, sw_zc + ROKLAND_SW_SLOT_L / 2.0,
    )
    # Wire entry channel connecting the switch pocket to the battery cavity
    sw_wire_channel = box_from_bounds(
        1.8, 7.0,
        1.0, 6.5,
        sw_zc - 3.5, sw_zc + 3.5,
    )

    cutouts = trimesh.boolean.union(
        [battery_cavity, sw_body_pocket, sw_actuator_slot, sw_wire_channel],
        engine="manifold",
    )
    return trimesh.boolean.difference([body, cutouts], engine="manifold")


def build_case_r1() -> trimesh.Trimesh:
    """Return the original bottom perimeter collar ring (CaseR1, 96.5 x 18.0 x 6.0 mm)."""
    return trimesh.load(os.path.join(REF_STL_DIR, "CaseR1.STL"))


def build_case_slide() -> trimesh.Trimesh:
    """Return the original bottom 8-pin magnetic pogo slide rail (CaseSlide / S2, 86.0 x 10.0 x 8.1 mm)."""
    return trimesh.load(os.path.join(REF_STL_DIR, "CaseSlide.STL"))
