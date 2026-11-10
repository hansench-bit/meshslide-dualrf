"""
Generator for CaseS1_DualRF (Dual-SMA: 915 MHz SMA + GPS SMA) and CaseS1_DualRF_BoltOn
(Outside-Mount 4-Bolt Square-Flange N-Type 915 MHz + GPS SMA).

Preserves 100% of the original MeshSlide CaseS1 lower tongue-and-groove mating rails,
left M2x4 countersunk screw mount, and right M2x5 brass insert leg, while shifting both RF ports
to the left (GPS SMA at X=48.50 mm, 915 MHz port at X=68.50 mm) on a clean, flush 18.0 mm wide
top deck (Z = -6.00 mm) completely clear of the right-side M2 screw boss ear (X=88.5..96.5 mm).

Provides two clean, 18.0 mm wide versions:
1. CaseS1_DualRF (Dual-SMA):
   - Uses a standard SMA Female bulkhead connector for 915 MHz LoRa (X=68.50 mm, Y=9.00 mm)
     and a standard SMA Female bulkhead connector for GPS (X=48.50 mm, Y=9.00 mm).
   - Both ports feature a Ø6.50 mm D-hole (5.90 mm anti-rotation flat) in the 2.80 mm top wall
     (Z = -6.00..-3.20 mm) and a full-depth, unbroken 6-sided 8.25 mm across-flats internal hex nut
     socket (Z = -3.20..+1.80 mm) opening into the unobstructed underside channel (Z >= +1.80 mm).
2. CaseS1_DualRF_BoltOn (Outside-Mount 4-Bolt N-Type + GPS SMA):
   - Flush 18.0 mm wide top deck (Z = -6.00 mm) for 4-hole square-flange ("outside-mount")
     N-Type Female panel-mount connectors (17.5x17.5 mm flange, 12.70x12.70 mm M2.5 4-bolt pattern,
     Ø10.60 mm center barrel bore) at X=68.50 mm, plus GPS SMA at X=48.50 mm.
"""

from __future__ import annotations
import os
import numpy as np
import trimesh
from cad.config import (
    REF_STL_DIR,
    N_TYPE_X,
    N_TYPE_Y,
    N_TYPE_BOLT_FLANGE_X,
    N_TYPE_BOLT_FLANGE_Y,
    N_TYPE_BOLT_GRID,
    N_TYPE_BOLT_CENTER_DIA,
    N_TYPE_BOLT_HOLE_DIA,
    N_TYPE_BOLT_NUT_AF,
    SMA_X,
    SMA_Y,
    SMA_HOLE_DIA,
    SMA_D_FLAT,
    SMA_HEX_AF,
    SMA_FLANGE_THICK,
    box_from_bounds,
    cylinder_z,
    d_hole_z,
    hex_prism_z,
)


def _build_flush_deck_base(z_top: float = -10.00) -> trimesh.Trimesh:
    """
    Build the shared 18.0 mm wide flush top deck body (Z = z_top to +1.80 mm)
    extending all the way to the right end face (X = 96.50 mm) so there is zero
    right-end undercut when printed vertically on X = 96.50 mm, plus widened
    clearance on the left rectangular latch slot (X = 20.40..36.80, Y = 5.70..11.50).
    """
    orig_s1 = trimesh.load(os.path.join(REF_STL_DIR, "CaseS1.STL"))

    # Completely fill both the old horizontal right-side SMA bore (X=86.5..96.5) AND its Ø11.6mm outer
    # circular counterbore (Y=3.2..14.8, Z=1.2..12.8) so the X=96.5mm end face is 100% smooth and flat,
    # and eliminate any trapped internal void at X=86.5..93.0mm for vertical printing!
    fill_sma_block = box_from_bounds(86.5, 96.5, 2.5, 15.5, -2.50, 13.0)
    fill_mid_bridge = box_from_bounds(46.0, 88.0, 4.0, 14.0, -2.50, 1.80)

    # Flush 18.0 mm wide flat deck spanning X = 49.5..96.50, Y = 0.0..18.0, Z = z_top..+1.80
    # Extending straight to X = 96.50 mm eliminates the right-end step/undercut when printing vertically!
    top_deck = box_from_bounds(49.5, 96.5, 0.0, 18.0, z_top, 1.80)

    left_ramp_verts = np.array([
        [49.5, 0.0, z_top],
        [49.5, 18.0, z_top],
        [SMA_X, 0.0, z_top],
        [SMA_X, 18.0, z_top],
        [40.0, 0.0, 0.0],
        [40.0, 18.0, 0.0],
        [SMA_X, 0.0, 0.0],
        [SMA_X, 18.0, 0.0],
    ], dtype=float)
    left_ramp = trimesh.convex.convex_hull(left_ramp_verts)

    merged = trimesh.boolean.union(
        [orig_s1, fill_sma_block, fill_mid_bridge, top_deck, left_ramp],
        engine="manifold",
    )

    # DFA Slip-Fit Clearances:
    # 1. Widen the rectangular top latch slot (X=20.30..38.60, Y=5.65..11.55, Z=-0.50..3.00) so CaseM1's
    #    entire ramped tongue (X=21.10..38.05, Y=6.00..11.20) has +0.35mm per side Y clearance and +0.6..0.8mm X clearance!
    slot_relief = box_from_bounds(20.30, 38.60, 5.65, 11.55, -0.50, 3.00)
    # 2. Add +0.20mm per side Y clearance along the inner CaseM1 sliding groove (X=0.0..46.5, Y=5.80..11.40, Z=1.75..4.50)
    channel_m1_relief = box_from_bounds(-0.20, 46.50, 5.80, 11.40, 1.75, 4.50)
    # 3. Add +0.20mm clearance on the right M2 mounting leg pocket step (X=90.30..96.60, Y=5.80..11.40, Z=12.80..13.20)
    right_leg_relief = box_from_bounds(90.30, 96.60, 5.80, 11.40, 12.80, 13.20)
    relief_union = trimesh.boolean.union([slot_relief, channel_m1_relief, right_leg_relief], engine="manifold")
    return trimesh.boolean.difference([merged, relief_union], engine="manifold")


def _build_45deg_bottom_channel(z_ceiling: float = -2.20) -> trimesh.Trimesh:
    """
    Build the internal bottom coax/connector insertion channel (X = 46.5..86.5, Y = 4.0..14.0)
    with a 45-degree sloped roof at X = 86.5 -> 83.0 mm so when CaseS1 is printed standing vertically
    on X = 96.50 mm, the internal channel transition prints support-free with zero bridging!
    """
    verts = np.array([
        [46.5, 4.0, z_ceiling], [46.5, 14.0, z_ceiling],
        [83.0, 4.0, z_ceiling], [83.0, 14.0, z_ceiling],
        [86.5, 4.0, z_ceiling + 3.5], [86.5, 14.0, z_ceiling + 3.5],
        [46.5, 4.0, 14.0], [46.5, 14.0, 14.0],
        [86.5, 4.0, 14.0], [86.5, 14.0, 14.0],
    ], dtype=float)
    return trimesh.convex.convex_hull(verts)


def build_case_s1_dual_rf() -> trimesh.Trimesh:
    """
    Build CaseS1_DualRF (Dual-SMA version: 915 MHz SMA at X=73.50 mm + GPS SMA at X=54.00 mm):
      - Flush 18.0 mm wide top deck raised to Z = -10.00 mm and extending to X = 96.50 mm (no undercut)
      - Internal underside ceiling raised 4.0 mm higher (Z = -2.20 mm) so the rigid coax ferrule clears the PCB
      - GPS SMA at X = 54.00 mm, Y = 9.00 mm:
          * Ø6.55 mm D-hole (6.05 mm flat) through 2.80 mm top wall (Z = -10.00..-7.20 mm)
          * Unbroken 6-sided 8.25 mm across-flats hex nut trap (Z = -7.20..-2.20 mm)
      - 915 MHz LoRa SMA at X = 73.50 mm, Y = 9.00 mm:
          * Ø6.55 mm D-hole (6.05 mm flat) through 2.80 mm top wall (Z = -10.00..-7.20 mm)
          * Unbroken 6-sided 8.25 mm across-flats hex nut trap (Z = -7.20..-2.20 mm)
      - Clean flat underside ceiling at Z = -2.20 mm with unobstructed bottom insertion channel
        (X = 46.5..85.0 mm, Y = 4.0..14.0 mm, Z = -2.20..14.0 mm).
    """
    z_top = -10.00
    body = _build_flush_deck_base(z_top=z_top)

    z_sma_cavity_top = z_top + SMA_FLANGE_THICK  # -7.20 mm
    z_ceiling = -2.20

    # 1. GPS SMA at X = 54.00, Y = 9.00
    gps_sma_dhole = d_hole_z(SMA_X, SMA_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    gps_sma_hex_trap = hex_prism_z(SMA_X, SMA_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 2. 915 MHz LoRa SMA at X = 73.50, Y = 9.00
    lora_sma_dhole = d_hole_z(N_TYPE_X, N_TYPE_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    lora_sma_hex_trap = hex_prism_z(N_TYPE_X, N_TYPE_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 3. Clean underside channel strictly below Z = -2.20 mm with 45-deg roof at X = 85.0 mm
    bottom_channel_clear = _build_45deg_bottom_channel(z_ceiling=z_ceiling)

    cutouts = trimesh.boolean.union(
        [gps_sma_dhole, gps_sma_hex_trap, lora_sma_dhole, lora_sma_hex_trap, bottom_channel_clear],
        engine="manifold",
    )

    result = trimesh.boolean.difference([body, cutouts], engine="manifold")
    result.merge_vertices()
    return result


def build_case_s1_dual_rf_bolton() -> trimesh.Trimesh:
    """
    Build CaseS1_DualRF_BoltOn for Outside-Mount 4-Hole Square-Flange N-Type Female panel-mount
    connectors (25.0-25.4 mm square flange, 18.30 mm center-to-center / 15.0 mm inside edge-to-edge
    M3 hole grid, Ø3.40 mm holes, Ø10.60 mm center bore, with 4x Captive M3 Hex Nut Sockets underneath):
      - Raised top deck at Z = -11.00 mm extending flush to X = 96.50 mm (eliminating right-end undercut)
      - Internal ceiling raised to Z = -2.20 mm so coax cords clear the internal PCB
      - GPS SMA at X = 54.00 mm, Y = 9.00 mm (with unbroken 6-sided 8.25 mm hex trap Z = -8.20..-2.20 mm)
      - Blended, rounded-corner 26.8 x 26.8 mm Flange Pad at X = 73.50 mm (Y = -4.40..+22.40 mm)
      - 4x Ø3.40 mm M3 clearance holes + 4x Captive 6-sided M3 Hex Nut Sockets (5.75 mm across flats)
      - Ø10.60 mm center coax bore at (73.50, 9.00)
    """
    z_top = -11.00
    z_ceiling = -2.20
    base_body = _build_flush_deck_base(z_top=z_top)

    half_grid = N_TYPE_BOLT_GRID / 2.0  # 9.15 mm
    r_corner = (N_TYPE_BOLT_FLANGE_Y - N_TYPE_BOLT_GRID) / 2.0  # (26.80 - 18.30)/2 = 4.25 mm
    z_edge_bot = -6.00

    corner_R_pillars = []
    for bx in [N_TYPE_X - half_grid, 96.50 - r_corner]:
        for sy in [-1.0, 1.0]:
            by = N_TYPE_Y + sy * half_grid
            corner_R_pillars.append(cylinder_z(bx, by, z_top, z_edge_bot, radius=r_corner, sections=48))
    # Extend the full 26.8 mm wide flange straight down to the X = 96.50 mm end face so there is zero undercut at the build plate!
    end_flange_block = box_from_bounds(96.50 - r_corner, 96.50, N_TYPE_Y - half_grid - r_corner, N_TYPE_Y + half_grid + r_corner, z_top, z_edge_bot)
    corner_R_pillars.append(end_flange_block)

    # Inner rail anchor prism blending smoothly into the 18.0 mm rail body (X = SMA_X..96.5 mm, Y = 0.0..18.0 mm)
    rail_anchor_verts = np.array([
        [SMA_X, 0.0, z_top], [SMA_X, 18.0, z_top],
        [96.5, 0.0, z_top], [96.5, 18.0, z_top],
        [SMA_X, 0.0, 1.80], [SMA_X, 18.0, 1.80],
        [96.5, 0.0, 1.80], [96.5, 18.0, 1.80],
    ], dtype=float)
    all_flange_verts = np.vstack([m.vertices for m in corner_R_pillars] + [rail_anchor_verts])
    blended_flange = trimesh.convex.convex_hull(all_flange_verts)

    body = trimesh.boolean.union([base_body, blended_flange], engine="manifold")

    # 1. Center coax barrel bore (Ø10.60 mm) at X = 73.50, Y = 9.00
    nt_center_bore = cylinder_z(N_TYPE_X, N_TYPE_Y, z_top - 1.0, 12.0, radius=N_TYPE_BOLT_CENTER_DIA / 2.0, sections=64)

    # 2. 4x Ø3.40 mm M3 corner bolt holes + 4x Captive M3 Hex Nut Sockets (5.75 mm AF) on 18.30 x 18.30 mm grid
    z_nut_ceiling = z_top + 3.00  # -8.00 mm (3.00 mm thick top clamped wall)
    bolt_and_nut_cuts = []
    for sx in [-1.0, 1.0]:
        for sy in [-1.0, 1.0]:
            bx = N_TYPE_X + sx * half_grid
            by = N_TYPE_Y + sy * half_grid
            bolt_and_nut_cuts.append(
                cylinder_z(bx, by, z_top - 1.0, z_nut_ceiling + 0.5, radius=N_TYPE_BOLT_HOLE_DIA / 2.0, sections=48)
            )
            bolt_and_nut_cuts.append(
                hex_prism_z(bx, by, z_nut_ceiling, z_ceiling, across_flats=N_TYPE_BOLT_NUT_AF)
            )

    # 3. SMA GPS vertical D-hole + unbroken 6-sided 8.25 mm hex nut trap at X = 54.00, Y = 9.00
    z_sma_cavity_top = z_top + SMA_FLANGE_THICK  # -8.20 mm
    sma_dhole = d_hole_z(SMA_X, SMA_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    sma_hex_trap = hex_prism_z(SMA_X, SMA_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 4. Clean underside channel strictly below Z = -2.20 mm with 45-deg roof at X = 85.0 mm
    bottom_channel_clear = _build_45deg_bottom_channel(z_ceiling=z_ceiling)

    cutouts = trimesh.boolean.union(
        [nt_center_bore, sma_dhole, sma_hex_trap, bottom_channel_clear] + bolt_and_nut_cuts,
        engine="manifold",
    )

    result = trimesh.boolean.difference([body, cutouts], engine="manifold")
    result.merge_vertices()
    return result


def build_case_s1_dual_rf_heatset() -> trimesh.Trimesh:
    """
    Build CaseS1_DualRF_Heatset for Outside-Mount 4-Hole Square-Flange N-Type Female panel-mount
    connectors using Top-Mounted M3 Brass Heat-Set Inserts (Ø4.00 mm x 5.00 mm deep blind bores
    with Ø4.30 mm top lead-in counterbore, leaving the sloped underside gusset 100% solid):
      - Raised top deck at Z = -11.00 mm extending flush to X = 96.50 mm (no right-end undercut)
      - Internal ceiling raised to Z = -2.20 mm so coax cords clear the internal PCB
      - GPS SMA at X = 54.00 mm, Y = 9.00 mm (with unbroken 6-sided 8.25 mm hex trap Z = -8.20..-2.20 mm)
      - Blended, rounded-corner 26.8 x 26.8 mm Flange Pad at X = 73.50 mm (Y = -4.40..+22.40 mm)
      - 4x Ø4.00 mm M3 heat-set insert bores (5.00 mm deep, Z = -11.00..-6.00 mm) + Ø4.30 mm x 0.50 mm
        self-centering lead-in + Ø3.20 mm screw tip relief to Z = -5.00 mm
      - Ø10.60 mm center coax bore at (73.50, 9.00)
    """
    z_top = -11.00
    z_ceiling = -2.20
    base_body = _build_flush_deck_base(z_top=z_top)

    half_grid = N_TYPE_BOLT_GRID / 2.0  # 9.15 mm
    r_corner = (N_TYPE_BOLT_FLANGE_Y - N_TYPE_BOLT_GRID) / 2.0  # 4.25 mm
    z_edge_bot = -6.00

    corner_R_pillars = []
    for bx in [N_TYPE_X - half_grid, 96.50 - r_corner]:
        for sy in [-1.0, 1.0]:
            by = N_TYPE_Y + sy * half_grid
            corner_R_pillars.append(cylinder_z(bx, by, z_top, z_edge_bot, radius=r_corner, sections=48))
    end_flange_block = box_from_bounds(96.50 - r_corner, 96.50, N_TYPE_Y - half_grid - r_corner, N_TYPE_Y + half_grid + r_corner, z_top, z_edge_bot)
    corner_R_pillars.append(end_flange_block)

    rail_anchor_verts = np.array([
        [SMA_X, 0.0, z_top], [SMA_X, 18.0, z_top],
        [96.5, 0.0, z_top], [96.5, 18.0, z_top],
        [SMA_X, 0.0, 1.80], [SMA_X, 18.0, 1.80],
        [96.5, 0.0, 1.80], [96.5, 18.0, 1.80],
    ], dtype=float)
    all_flange_verts = np.vstack([m.vertices for m in corner_R_pillars] + [rail_anchor_verts])
    blended_flange = trimesh.convex.convex_hull(all_flange_verts)

    body = trimesh.boolean.union([base_body, blended_flange], engine="manifold")

    # 1. Center coax barrel bore (Ø10.60 mm) at X = 73.50, Y = 9.00
    nt_center_bore = cylinder_z(N_TYPE_X, N_TYPE_Y, z_top - 1.0, 12.0, radius=N_TYPE_BOLT_CENTER_DIA / 2.0, sections=64)

    # 2. 4x Top-Mount M3 Heat-Set Insert Bores (Ø4.00 mm x 5.00 mm deep + Ø4.30 mm lead-in + Ø3.20 mm tip relief)
    heatset_cuts = []
    for sx in [-1.0, 1.0]:
        for sy in [-1.0, 1.0]:
            bx = N_TYPE_X + sx * half_grid
            by = N_TYPE_Y + sy * half_grid
            heatset_cuts.append(cylinder_z(bx, by, z_top - 1.0, z_top + 0.50, radius=4.30 / 2.0, sections=48))
            heatset_cuts.append(cylinder_z(bx, by, z_top - 0.5, z_top + 5.00, radius=4.00 / 2.0, sections=48))
            heatset_cuts.append(cylinder_z(bx, by, z_top + 4.50, z_top + 6.00, radius=3.20 / 2.0, sections=48))

    # 3. SMA GPS vertical D-hole + unbroken 6-sided 8.25 mm hex nut trap at X = 54.00, Y = 9.00
    z_sma_cavity_top = z_top + SMA_FLANGE_THICK  # -8.20 mm
    sma_dhole = d_hole_z(SMA_X, SMA_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    sma_hex_trap = hex_prism_z(SMA_X, SMA_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 4. Clean underside channel strictly below Z = -2.20 mm with 45-deg roof at X = 85.0 mm
    bottom_channel_clear = _build_45deg_bottom_channel(z_ceiling=z_ceiling)

    cutouts = trimesh.boolean.union(
        [nt_center_bore, sma_dhole, sma_hex_trap, bottom_channel_clear] + heatset_cuts,
        engine="manifold",
    )

    result = trimesh.boolean.difference([body, cutouts], engine="manifold")
    result.merge_vertices()
    return result


