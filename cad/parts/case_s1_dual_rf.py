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


def _build_flush_deck_base(z_top: float = -6.00) -> trimesh.Trimesh:
    """
    Build the shared 18.0 mm wide flush top deck body (Z = z_top to +1.80 mm)
    with aerodynamic 45-deg side ramps and a completely flush, smooth right-end face (X = 96.5 mm).
    """
    orig_s1 = trimesh.load(os.path.join(REF_STL_DIR, "CaseS1.STL"))

    # Completely fill both the old horizontal right-side SMA bore (X=93.0..96.5) AND its Ø11.6mm outer
    # circular counterbore (Y=3.2..14.8, Z=1.2..12.8) so the X=96.5mm end face is 100% smooth and flat!
    fill_sma_block = box_from_bounds(93.0, 96.5, 2.5, 15.5, 0.8, 13.0)
    fill_mid_bridge = box_from_bounds(42.6, 81.0, 4.0, 14.0, 0.0, 1.80)

    # Flush 18.0 mm wide flat deck spanning X = 42.6..81.0, Y = 0.0..18.0, Z = z_top..+1.80
    top_deck = box_from_bounds(42.6, 81.0, 0.0, 18.0, z_top, 1.80)

    left_ramp_verts = np.array([
        [42.6, 0.0, z_top],
        [42.6, 18.0, z_top],
        [SMA_X, 0.0, z_top],
        [SMA_X, 18.0, z_top],
        [36.5, 0.0, 0.0],
        [36.5, 18.0, 0.0],
        [SMA_X, 0.0, 0.0],
        [SMA_X, 18.0, 0.0],
    ], dtype=float)
    left_ramp = trimesh.convex.convex_hull(left_ramp_verts)

    right_ramp_verts = np.array([
        [75.0, 0.0, z_top],
        [75.0, 18.0, z_top],
        [81.0, 0.0, z_top],
        [81.0, 18.0, 0.0],
        [75.0, 0.0, 0.0],
        [75.0, 18.0, 0.0],
        [87.0, 0.0, 0.0],
        [87.0, 18.0, 0.0],
    ], dtype=float)
    right_ramp = trimesh.convex.convex_hull(right_ramp_verts)

    return trimesh.boolean.union(
        [orig_s1, fill_sma_block, fill_mid_bridge, top_deck, left_ramp, right_ramp],
        engine="manifold",
    )


def build_case_s1_dual_rf() -> trimesh.Trimesh:
    """
    Build CaseS1_DualRF (Dual-SMA version: 915 MHz SMA at X=68.50 mm + GPS SMA at X=48.50 mm):
      - Flush 18.0 mm wide top deck at Z = -6.00 mm (zero exterior overhang)
      - GPS SMA at X = 48.50 mm, Y = 9.00 mm:
          * Ø6.50 mm D-hole (5.90 mm flat) through 2.80 mm top wall (Z = -6.00..-3.20 mm)
          * Unbroken 6-sided 8.25 mm across-flats hex nut trap (Z = -3.20..+1.80 mm)
      - 915 MHz LoRa SMA at X = 68.50 mm, Y = 9.00 mm:
          * Ø6.50 mm D-hole (5.90 mm flat) through 2.80 mm top wall (Z = -6.00..-3.20 mm)
          * Unbroken 6-sided 8.25 mm across-flats hex nut trap (Z = -3.20..+1.80 mm)
      - Clean flat underside ceiling at Z = +1.80 mm with unobstructed bottom insertion channel
        (X = 42.6..78.5 mm, Y = 3.5..14.5 mm, Z = +1.80..14.0 mm) so both SMA connectors push
        straight in from underneath.
    """
    z_top = -6.00
    body = _build_flush_deck_base(z_top=z_top)

    z_sma_cavity_top = z_top + SMA_FLANGE_THICK  # -3.20 mm

    # 1. GPS SMA at X = 48.50, Y = 9.00
    gps_sma_dhole = d_hole_z(SMA_X, SMA_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    gps_sma_hex_trap = hex_prism_z(SMA_X, SMA_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 2. 915 MHz LoRa SMA at X = 68.50, Y = 9.00
    lora_sma_dhole = d_hole_z(N_TYPE_X, N_TYPE_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    lora_sma_hex_trap = hex_prism_z(N_TYPE_X, N_TYPE_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 3. Clean underside channel strictly below Z = +1.80 mm so the hex sockets (Z = -3.20..+1.80 mm)
    # remain 100% intact 6-sided hexagons all the way down to the Z = +1.80 mm ceiling
    bottom_channel_clear = box_from_bounds(42.6, 78.5, 4.0, 14.0, 1.80, 14.0)

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
      - GPS SMA at X = 48.50 mm, Y = 9.00 mm (with unbroken 6-sided 8.25 mm hex trap Z = -4.40..+1.80 mm)
      - Blended, rounded-corner 26.8 x 26.8 mm Flange Pad (Y = -4.40..+22.40 mm, Z = -7.20..-2.20 mm outer edge)
        with smooth 45-deg Y-Z underside gussets blending down into the Y = 0..18 mm rail at Z = +1.80 mm,
        plus smooth X-Y side transition tapers on both ends (X = 48.5..59.35 mm and X = 77.65..85.5 mm).
      - 4x Ø3.40 mm M3 clearance holes at (68.50 ± 9.15, 9.00 ± 9.15) through 3.00 mm top plate (Z = -7.20..-4.20 mm)
      - 4x Captive 6-sided M3 Hex Nut Sockets (5.75 mm across flats, Z = -4.20..+1.80 mm) recessed into the blended gusset
      - Ø10.60 mm center coax bore at (68.50, 9.00)
    """
    z_top = -7.20
    base_body = _build_flush_deck_base(z_top=z_top)

    # Construct the blended, rounded-corner N-Type Flange Pad + Underside Sloped Gusset:
    # 4 corner cylinders (radius = 4.25 mm) at the 4 M3 bolt centers (59.35, 77.65) x (-0.15, 18.15)
    # span X = 55.10..81.90 mm, Y = -4.40..+22.40 mm (26.80 mm total Y width) from Z = -7.20 to -2.20 mm,
    # and blend smoothly inward to the 18.0 mm rail body (X = 48.50..85.00 mm, Y = 0.00..18.00 mm) at Z = +1.80 mm!
    half_grid = N_TYPE_BOLT_GRID / 2.0  # 9.15 mm
    r_corner = (N_TYPE_BOLT_FLANGE_Y - N_TYPE_BOLT_GRID) / 2.0  # (26.80 - 18.30)/2 = 4.25 mm
    z_edge_bot = -2.20

    corner_R_pillars = []
    for sx in [-1.0, 1.0]:
        for sy in [-1.0, 1.0]:
            bx = N_TYPE_X + sx * half_grid
            by = N_TYPE_Y + sy * half_grid
            corner_R_pillars.append(cylinder_z(bx, by, z_top, z_edge_bot, radius=r_corner, sections=48))

    # Inner rail anchor prism (X = 48.50..85.00 mm, Y = 0.00..18.00 mm, Z = z_top..+1.80 mm, tapering to Z=0 at X=87.0)
    rail_anchor_verts = np.array([
        [SMA_X, 0.0, z_top], [SMA_X, 18.0, z_top],
        [81.0, 0.0, z_top], [81.0, 18.0, z_top],
        [SMA_X, 0.0, 1.80], [SMA_X, 18.0, 1.80],
        [83.5, 0.0, 1.80], [83.5, 18.0, 1.80],
        [87.0, 0.0, 0.0], [87.0, 18.0, 0.0],
    ], dtype=float)
    all_flange_verts = np.vstack([m.vertices for m in corner_R_pillars] + [rail_anchor_verts])
    blended_flange = trimesh.convex.convex_hull(all_flange_verts)

    body = trimesh.boolean.union([base_body, blended_flange], engine="manifold")

    # 1. Center coax barrel bore (Ø10.60 mm) at X = 68.50, Y = 9.00
    nt_center_bore = cylinder_z(N_TYPE_X, N_TYPE_Y, z_top - 1.0, 12.0, radius=N_TYPE_BOLT_CENTER_DIA / 2.0, sections=64)

    # 2. 4x Ø3.40 mm M3 corner bolt holes + 4x Captive M3 Hex Nut Sockets (5.75 mm AF) on 18.30 x 18.30 mm grid
    z_nut_ceiling = z_top + 3.00  # -4.20 mm (3.00 mm thick top clamped wall)
    bolt_and_nut_cuts = []
    for sx in [-1.0, 1.0]:
        for sy in [-1.0, 1.0]:
            bx = N_TYPE_X + sx * half_grid
            by = N_TYPE_Y + sy * half_grid
            # M3 screw clearance hole through top wall (Z = -7.20 to -4.20 mm)
            bolt_and_nut_cuts.append(
                cylinder_z(bx, by, z_top - 1.0, z_nut_ceiling + 0.5, radius=N_TYPE_BOLT_HOLE_DIA / 2.0, sections=48)
            )
            # 6-sided Captive M3 Hex Nut Socket (Z = -4.20 to +1.80 mm) recessed into the sloped underside gusset
            bolt_and_nut_cuts.append(
                hex_prism_z(bx, by, z_nut_ceiling, 1.80, across_flats=N_TYPE_BOLT_NUT_AF)
            )

    # 3. SMA GPS vertical D-hole + unbroken 6-sided 8.25 mm hex nut trap at X = 48.50, Y = 9.00
    z_sma_cavity_top = z_top + SMA_FLANGE_THICK  # -4.40 mm
    sma_dhole = d_hole_z(SMA_X, SMA_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    sma_hex_trap = hex_prism_z(SMA_X, SMA_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 4. Clean underside channel strictly below Z = +1.80 mm
    bottom_channel_clear = box_from_bounds(42.6, 78.5, 4.0, 14.0, 1.80, 14.0)

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
      - GPS SMA at X = 48.50 mm, Y = 9.00 mm (with unbroken 6-sided 8.25 mm hex trap Z = -4.40..+1.80 mm)
      - Blended, rounded-corner 26.8 x 26.8 mm Flange Pad (Y = -4.40..+22.40 mm, Z = -7.20..-2.20 mm outer edge)
        with smooth 45-deg Y-Z underside gussets blending down into the Y = 0..18 mm rail at Z = +1.80 mm
      - 4x Ø4.00 mm M3 heat-set insert bores (5.00 mm deep, Z = -7.20..-2.20 mm) + Ø4.30 mm x 0.50 mm
        self-centering lead-in + Ø3.20 mm screw tip relief to Z = -1.20 mm at (68.50 ± 9.15, 9.00 ± 9.15)
      - Ø10.60 mm center coax bore at (68.50, 9.00)
    """
    z_top = -7.20
    base_body = _build_flush_deck_base(z_top=z_top)

    half_grid = N_TYPE_BOLT_GRID / 2.0  # 9.15 mm
    r_corner = (N_TYPE_BOLT_FLANGE_Y - N_TYPE_BOLT_GRID) / 2.0  # 4.25 mm
    z_edge_bot = -2.20

    corner_R_pillars = []
    for sx in [-1.0, 1.0]:
        for sy in [-1.0, 1.0]:
            bx = N_TYPE_X + sx * half_grid
            by = N_TYPE_Y + sy * half_grid
            corner_R_pillars.append(cylinder_z(bx, by, z_top, z_edge_bot, radius=r_corner, sections=48))

    rail_anchor_verts = np.array([
        [SMA_X, 0.0, z_top], [SMA_X, 18.0, z_top],
        [81.0, 0.0, z_top], [81.0, 18.0, z_top],
        [SMA_X, 0.0, 1.80], [SMA_X, 18.0, 1.80],
        [83.5, 0.0, 1.80], [83.5, 18.0, 1.80],
        [87.0, 0.0, 0.0], [87.0, 18.0, 0.0],
    ], dtype=float)
    all_flange_verts = np.vstack([m.vertices for m in corner_R_pillars] + [rail_anchor_verts])
    blended_flange = trimesh.convex.convex_hull(all_flange_verts)

    body = trimesh.boolean.union([base_body, blended_flange], engine="manifold")

    # 1. Center coax barrel bore (Ø10.60 mm) at X = 68.50, Y = 9.00
    nt_center_bore = cylinder_z(N_TYPE_X, N_TYPE_Y, z_top - 1.0, 12.0, radius=N_TYPE_BOLT_CENTER_DIA / 2.0, sections=64)

    # 2. 4x Top-Mount M3 Heat-Set Insert Bores (Ø4.00 mm x 5.00 mm deep + Ø4.30 mm lead-in + Ø3.20 mm tip relief)
    heatset_cuts = []
    for sx in [-1.0, 1.0]:
        for sy in [-1.0, 1.0]:
            bx = N_TYPE_X + sx * half_grid
            by = N_TYPE_Y + sy * half_grid
            # Top self-centering lead-in (Ø4.30 mm, 0.50 mm deep: Z = -7.20 to -6.70 mm)
            heatset_cuts.append(cylinder_z(bx, by, z_top - 1.0, z_top + 0.50, radius=4.30 / 2.0, sections=48))
            # Main M3 heat-set insert bore (Ø4.00 mm, 5.00 mm deep: Z = -7.20 to -2.20 mm)
            heatset_cuts.append(cylinder_z(bx, by, z_top - 0.5, z_top + 5.00, radius=4.00 / 2.0, sections=48))
            # Bottom M3 screw tip relief (Ø3.20 mm, down to Z = -1.20 mm, keeping underside gusset closed!)
            heatset_cuts.append(cylinder_z(bx, by, z_top + 4.50, -1.20, radius=3.20 / 2.0, sections=48))

    # 3. SMA GPS vertical D-hole + unbroken 6-sided 8.25 mm hex nut trap at X = 48.50, Y = 9.00
    z_sma_cavity_top = z_top + SMA_FLANGE_THICK  # -4.40 mm
    sma_dhole = d_hole_z(SMA_X, SMA_Y, z_top - 1.0, z_sma_cavity_top + 0.5, SMA_HOLE_DIA, SMA_D_FLAT, sections=64)
    sma_hex_trap = hex_prism_z(SMA_X, SMA_Y, z_sma_cavity_top, 10.0, across_flats=SMA_HEX_AF)

    # 4. Clean underside channel strictly below Z = +1.80 mm
    bottom_channel_clear = box_from_bounds(42.6, 78.5, 4.0, 14.0, 1.80, 14.0)

    cutouts = trimesh.boolean.union(
        [nt_center_bore, sma_dhole, sma_hex_trap, bottom_channel_clear] + heatset_cuts,
        engine="manifold",
    )

    result = trimesh.boolean.difference([body, cutouts], engine="manifold")
    result.merge_vertices()
    return result


