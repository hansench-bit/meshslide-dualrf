"""
Parametric generator for the CardKB Pro Hybrid Enclosure System:
- Combines HarukiToreda's continuous dust-sealing elastomer actuator membrane (TPU Base Mat)
  with Printables #1512657's rigid PETG/PLA tactile keycaps in an ultra-slim no-Grove-port profile.
- Uses a back-loaded flanged button + bezel-bar legend architecture:
  1. All 46 main concave buttons are identical & interchangeable when back-loading into the bezel.
  2. Character & function legends live on the horizontal bezel bars directly above each key row.
  3. Includes both a 1-piece flex-bridged drop-in button tray and loose individual buttons.
  4. Provides both the MeshSlide SlideKB_Pro module (KB_S1_Pro + KB_S3_Pro with internal wire channel
     to the pogo rail) and a Standalone Ultra-Slim enclosure (CardKB_Standalone_Bezel + Back).
"""

from __future__ import annotations
import os
import math
import tempfile
import numpy as np
import trimesh

from cad.config import (
    REF_STL_DIR,
    OUT_STL_DIR,
    CARDKB_PCB_W,
    CARDKB_PCB_H,
    CARDKB_PCB_T,
    CARDKB_SMD_SW_H,
    CARDKB_S1_PCB_X0,
    CARDKB_S1_PCB_Z0,
    CARDKB_COL_XS_12,
    CARDKB_COL_XS_11,
    CARDKB_ROW_YS,
    CARDKB_DPAD_UP,
    CARDKB_DPAD_DOWN,
    CARDKB_DPAD_LEFT,
    CARDKB_DPAD_RIGHT,
    CARDKB_RGB_LED_XY,
    CARDKB_LEGO_LOWER_XY,
    CARDKB_LEGO_UPPER_XY,
    CARDKB_KEY_SHAFT_W,
    CARDKB_KEY_SHAFT_H,
    CARDKB_BEZEL_CLEARANCE,
    CARDKB_KEY_FLANGE_W,
    CARDKB_KEY_FLANGE_H,
    CARDKB_KEY_FLANGE_T,
    CARDKB_DPAD_SHAFT_W,
    CARDKB_DPAD_SHAFT_H,
    CARDKB_DPAD_FLANGE_W,
    CARDKB_DPAD_FLANGE_H,
    CARDKB_TPU_MEMBRANE_T,
    CARDKB_TPU_PLUNGER_DIA,
    box_from_bounds,
    cylinder_z,
)

# Row legend strings for the 4 horizontal bezel bars (Top row 0 -> Bottom row 3)
ROW_LEGENDS: list[list[str]] = [
    ["ESC", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "DEL"],
    ["TAB", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "FN"],
    ["SHF", "A", "S", "D", "F", "G", "H", "J", "K", "L", "ENT"],
    ["SYM", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "SPC"],
]


def get_all_50_switch_centers() -> list[tuple[float, float, bool]]:
    """
    Return all 50 switch centers in CardKB Local PCB Coordinates (X_pcb, Y_pcb, is_dpad):
      - 46 main matrix keys (Rows 0..1 have 12 keys; Rows 2..3 have 11 keys)
      - 4 D-pad directional keys on the lower-left
    """
    pts: list[tuple[float, float, bool]] = []
    for r_idx, ry in enumerate(CARDKB_ROW_YS):
        xs = CARDKB_COL_XS_12 if r_idx < 2 else CARDKB_COL_XS_11
        for kx in xs:
            pts.append((kx, ry, False))
    for dx, dy in [CARDKB_DPAD_UP, CARDKB_DPAD_DOWN, CARDKB_DPAD_LEFT, CARDKB_DPAD_RIGHT]:
        pts.append((dx, dy, True))
    return pts


def pcb_to_s1_transform(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """
    Proper rigid-body transformation (det = +1) mapping CardKB Local PCB coordinates
    (X_pcb in [0..84], Y_pcb in [0..54], Z_pcb where 0.0 is PCB top surface and +6.40 is Bezel front face)
    into MeshSlide KB_S1_Pro coordinates:
      X_S1 = 64.90 - Y_pcb
      Y_S1 = 0.60  + Z_pcb
      Z_S1 = 90.00 - X_pcb
    """
    m = mesh.copy()
    T = np.array([
        [0.0, -1.0,  0.0, 64.90],
        [0.0,  0.0,  1.0,  0.60],
        [-1.0, 0.0,  0.0, 90.00],
        [0.0,  0.0,  0.0,  1.00],
    ], dtype=float)
    m.apply_transform(T)
    return m


def rounded_box_z(
    xc: float, yc: float, w: float, h: float, zmin: float, zmax: float, radius: float = 0.65, sections: int = 24
) -> trimesh.Trimesh:
    """Create a vertical prism with rounded Z-edges centered at (xc, yc) spanning [zmin..zmax]."""
    r = min(radius, w / 2.0 - 0.05, h / 2.0 - 0.05)
    if r <= 0.05:
        return box_from_bounds(xc - w / 2.0, xc + w / 2.0, yc - h / 2.0, yc + h / 2.0, zmin, zmax)
    dx = w / 2.0 - r
    dy = h / 2.0 - r
    pts = []
    n_corner = max(4, sections // 4)
    for cx, cy, a0 in [
        (xc + dx, yc + dy, 0.0),
        (xc - dx, yc + dy, math.pi / 2.0),
        (xc - dx, yc - dy, math.pi),
        (xc + dx, yc - dy, 1.5 * math.pi),
    ]:
        for i in range(n_corner):
            ang = a0 + (math.pi / 2.0) * (i / n_corner)
            pts.append([cx + r * math.cos(ang), cy + r * math.sin(ang), zmin])
            pts.append([cx + r * math.cos(ang), cy + r * math.sin(ang), zmax])
    return trimesh.convex.convex_hull(np.array(pts, dtype=float))


# ---------------------------------------------------------------------------
# 1. Continuous TPU Base Mat (KB_TPU_Mat) — Fits both SlideKB_Pro & Standalone
# ---------------------------------------------------------------------------
def build_kb_tpu_mat() -> trimesh.Trimesh:
    """
    Build the continuous flexible TPU 95A/85A actuator mat (83.6 x 53.6 mm footprint) in Local PCB coords:
      - Z_pcb = 0.00..2.10 mm: Underside PCB standoff grid ribs & perimeter gasket resting on bare FR4 PCB
        (with top-left clearance pocket for ATmega8A MCU + direct-soldered wire pads)
      - Z_pcb = 1.40..2.10 mm: 50 cylindrical switch actuator plungers (Ø2.60 mm) centered over the 50 SMD switches
      - Z_pcb = 2.10..2.80 mm: Continuous 0.70 mm dust-sealing TPU membrane (thinned to 0.35 mm in flex rings)
      - Z_pcb = 2.80..3.10 mm: 50 top button-registration pads (2.50 x 2.50 x 0.30 mm) mating with button bases
    """
    margin = 0.20  # 0.20mm per-side clearance inside 84.0 x 54.0 mm pocket -> 83.6 x 53.6 mm mat
    x0, x1 = margin, CARDKB_PCB_W - margin
    y0, y1 = margin, CARDKB_PCB_H - margin

    # Main continuous membrane sheet (Z = 2.10..2.80 mm)
    membrane = box_from_bounds(x0, x1, y0, y1, 2.10, 2.80)

    # Underside perimeter gasket & standoff grid ribs (Z = 0.00..2.15 mm)
    rim_outer = box_from_bounds(x0, x1, y0, y1, 0.00, 2.15)
    rim_inner = box_from_bounds(x0 + 1.40, x1 - 1.40, y0 + 1.40, y1 - 1.40, -0.10, 2.20)
    perimeter_gasket = trimesh.boolean.difference([rim_outer, rim_inner], engine="manifold")

    ribs = [perimeter_gasket]
    # Horizontal support ribs between the 4 switch rows
    for ry_rib in [12.70, 24.70, 36.70, 48.20]:
        ribs.append(box_from_bounds(13.0, x1 - 1.0, ry_rib - 0.55, ry_rib + 0.55, 0.00, 2.15))
    # Vertical support ribs between switch columns
    for c in range(13):
        rx_rib = 12.30 + c * 6.00
        if rx_rib < x1 - 0.8:
            ribs.append(box_from_bounds(rx_rib - 0.38, rx_rib + 0.38, y0 + 1.0, 48.50, 0.00, 2.15))
    # D-pad surround rib
    ribs.append(box_from_bounds(12.20, 13.00, y0 + 1.0, 20.50, 0.00, 2.15))
    ribs.append(box_from_bounds(x0 + 1.0, 13.00, 19.50, 20.40, 0.00, 2.15))

    # Lego registration boss on underside (around lower Lego hole at X=6.90, Y=37.10)
    lx, ly = CARDKB_LEGO_LOWER_XY
    ribs.append(cylinder_z(lx, ly, 0.00, 2.15, radius=3.80, sections=36))

    # 50 underside cylindrical switch plungers (Z = 1.42..2.15 mm, Ø2.60 mm) + 50 top registration pads (Z = 2.75..3.10 mm)
    plungers_and_pads = []
    flex_ring_cuts = []
    switch_body_clearances = []
    for kx, ky, is_dpad in get_all_50_switch_centers():
        # Clear any rib/perimeter gasket within 3.6 x 3.6 mm around each SMD switch body (Z = -0.10..2.10 mm)
        switch_body_clearances.append(box_from_bounds(kx - 1.80, kx + 1.80, ky - 1.80, ky + 1.80, -0.10, 2.10))
        # Underside plunger pressing SMD switch dome
        plungers_and_pads.append(cylinder_z(kx, ky, 1.42, 2.15, radius=CARDKB_TPU_PLUNGER_DIA / 2.0, sections=28))
        # Top button-registration pad (2.50 x 2.50 x 0.30 mm)
        plungers_and_pads.append(rounded_box_z(kx, ky, 2.50, 2.50, 2.75, 3.10, radius=0.40, sections=16))

        # Elastic flex ring groove on top of membrane (Z = 2.45..2.85 mm)
        ow = 4.50 if not is_dpad else 4.10
        oh = 4.80 if not is_dpad else 3.70
        iw = 3.20 if not is_dpad else 2.90
        ih = 3.40 if not is_dpad else 2.70
        ring_out = rounded_box_z(kx, ky, ow, oh, 2.45, 2.85, radius=0.55, sections=16)
        ring_in = rounded_box_z(kx, ky, iw, ih, 2.40, 2.90, radius=0.45, sections=16)
        flex_ring_cuts.append(trimesh.boolean.difference([ring_out, ring_in], engine="manifold"))

    ribs_cleared = trimesh.boolean.difference(
        [trimesh.boolean.union(ribs, engine="manifold"), trimesh.boolean.union(switch_body_clearances, engine="manifold")],
        engine="manifold",
    )
    body = trimesh.boolean.union([membrane, ribs_cleared] + plungers_and_pads, engine="manifold")

    # Carve out:
    # 1) Top-left underside clearance pocket for ATmega8A MCU & direct-soldered Grove pads (X=1.6..12.2, Y=20.4..52.4, Z=-0.1..2.10)
    #    (while keeping the Lego registration boss at X=6.90, Y=37.10)
    mcu_pocket = box_from_bounds(1.60, 12.20, 20.40, 52.40, -0.10, 2.10)
    lego_keep = cylinder_z(lx, ly, -0.20, 2.20, radius=3.80, sections=36)
    mcu_pocket = trimesh.boolean.difference([mcu_pocket, lego_keep], engine="manifold")

    # 2) Lego registration through-hole (Ø4.90 mm at X=6.90, Y=37.10)
    lego_hole = cylinder_z(lx, ly, -0.20, 3.50, radius=2.45, sections=36)

    # 3) Top-left wire exit notch on perimeter rim (X=2.2..8.5, Y=51.5..54.0, Z=-0.1..2.10) for 4 direct-soldered wires
    wire_notch = box_from_bounds(2.20, 8.50, 51.50, 54.00, -0.10, 2.10)

    # 4) Translucent thin window over RGB Status LED (X=15.55, Y=21.32, thins membrane to 0.35 mm)
    led_x, led_y = CARDKB_RGB_LED_XY
    led_recess = cylinder_z(led_x, led_y, -0.10, 2.45, radius=1.30, sections=24)

    all_cuts = trimesh.boolean.union(flex_ring_cuts + [mcu_pocket, lego_hole, wire_notch, led_recess], engine="manifold")
    mat = trimesh.boolean.difference([body, all_cuts], engine="manifold")
    mat.merge_vertices()
    return mat


# ---------------------------------------------------------------------------
# 2. Back-Loaded Rigid PETG/PLA Buttons (Single, Loose Set, and Bridged Tray)
# ---------------------------------------------------------------------------
def _make_single_button_at(
    kx: float, ky: float, is_dpad: bool = False, has_homing: bool = False, dpad_dir: str = ""
) -> trimesh.Trimesh:
    """
    Create a single back-loaded rigid PETG/PLA button in Local PCB Z-coordinates:
      - Z_pcb = 2.90..3.50 mm: Retaining flange (5.40 x 5.70 x 0.60 mm main; 5.00 x 4.60 x 0.60 mm D-pad)
      - Z_pcb = 3.50..6.95 mm: Vertical button shaft (4.30 x 4.60 mm main; 4.00 x 3.60 mm D-pad)
        (protrudes 0.55 mm above Z_pcb = 6.40 mm Bezel top surface)
      - Top face (Z_pcb = 6.55..6.95 mm): Concave finger recess + optional homing bar
      - Underside (Z_pcb = 2.90..3.22 mm): 2.75 x 2.75 x 0.32 mm socket mating onto TPU registration pad
    """
    fw = CARDKB_DPAD_FLANGE_W if is_dpad else CARDKB_KEY_FLANGE_W
    fh = CARDKB_DPAD_FLANGE_H if is_dpad else CARDKB_KEY_FLANGE_H
    sw = CARDKB_DPAD_SHAFT_W if is_dpad else CARDKB_KEY_SHAFT_W
    sh = CARDKB_DPAD_SHAFT_H if is_dpad else CARDKB_KEY_SHAFT_H

    flange = rounded_box_z(kx, ky, fw, fh, 2.90, 3.50, radius=0.75, sections=20)
    shaft = rounded_box_z(kx, ky, sw, sh, 3.45, 6.95, radius=0.60, sections=20)
    parts = [flange, shaft]

    # Concave finger dish carved out of top face (Z_pcb = 6.58..7.05)
    dish_verts = []
    dw = (sw - 1.10) / 2.0
    dh = (sh - 1.10) / 2.0
    for z_val, scale in [(6.58, 0.45), (6.75, 0.80), (7.02, 1.05)]:
        for i in range(24):
            ang = 2.0 * math.pi * i / 24.0
            dish_verts.append([kx + dw * scale * math.cos(ang), ky + dh * scale * math.sin(ang), z_val])
    dish = trimesh.convex.convex_hull(np.array(dish_verts, dtype=float))

    # Bottom registration socket (2.75 x 2.75 x 0.32 mm at Z_pcb = 2.85..3.22 mm)
    bot_socket = rounded_box_z(kx, ky, 2.75, 2.75, 2.85, 3.22, radius=0.40, sections=16)

    btn = trimesh.boolean.difference([trimesh.boolean.union(parts, engine="manifold"), dish, bot_socket], engine="manifold")

    # Add tactile homing bar on F and J (or directional bar on D-pad)
    if has_homing:
        hbar = box_from_bounds(kx - 0.85, kx + 0.85, ky - 1.35, ky - 0.95, 6.50, 6.98)
        btn = trimesh.boolean.union([btn, hbar], engine="manifold")
    elif dpad_dir in ("UP", "DOWN"):
        hbar = box_from_bounds(kx - 0.80, kx + 0.80, ky - 0.25, ky + 0.25, 6.50, 6.98)
        btn = trimesh.boolean.union([btn, hbar], engine="manifold")
    elif dpad_dir in ("LEFT", "RIGHT"):
        vbar = box_from_bounds(kx - 0.25, kx + 0.25, ky - 0.70, ky + 0.70, 6.50, 6.98)
        btn = trimesh.boolean.union([btn, vbar], engine="manifold")

    return btn


def build_kb_button_single() -> trimesh.Trimesh:
    """Build a single loose flanged concave main button centered and flat on Z=0 for spare printing."""
    b = _make_single_button_at(0.0, 0.0, is_dpad=False, has_homing=False)
    bmin = b.bounds[0]
    b.apply_translation([-bmin[0], -bmin[1], -bmin[2]])
    b.merge_vertices()
    return b


def build_kb_buttons_loose_set() -> trimesh.Trimesh:
    """Build all 50 back-loaded flanged concave buttons (46 main + 4 D-pad) in their exact matrix positions."""
    btns = []
    for r_idx, ry in enumerate(CARDKB_ROW_YS):
        xs = CARDKB_COL_XS_12 if r_idx < 2 else CARDKB_COL_XS_11
        for c_idx, kx in enumerate(xs):
            lbl = ROW_LEGENDS[r_idx][c_idx]
            btns.append(_make_single_button_at(kx, ry, is_dpad=False, has_homing=(lbl in ("F", "J"))))
    for (dx, dy), ddir in [
        (CARDKB_DPAD_UP, "UP"),
        (CARDKB_DPAD_DOWN, "DOWN"),
        (CARDKB_DPAD_LEFT, "LEFT"),
        (CARDKB_DPAD_RIGHT, "RIGHT"),
    ]:
        btns.append(_make_single_button_at(dx, dy, is_dpad=True, dpad_dir=ddir))
    res = trimesh.boolean.union(btns, engine="manifold")
    res.merge_vertices()
    return res


def build_kb_buttons_bridged() -> trimesh.Trimesh:
    """
    Build the 1-piece drop-in button array where all 46 main keys + 4 D-pad keys are connected at the
    flange level (Z_pcb = 2.90..3.16 mm) by compliant 0.44 x 0.26 mm flexible bridges so all 50 keys
    drop into the back of the bezel in a single step without sorting loose parts.
    """
    loose = build_kb_buttons_loose_set()
    bridges = []
    # Horizontal bridges along each of the 4 rows
    for r_idx, ry in enumerate(CARDKB_ROW_YS):
        xs = CARDKB_COL_XS_12 if r_idx < 2 else CARDKB_COL_XS_11
        for i in range(len(xs) - 1):
            bridges.append(box_from_bounds(xs[i] + 2.50, xs[i + 1] - 2.50, ry - 0.22, ry + 0.22, 2.90, 3.16))
    # Vertical bridges between rows for Columns 1..11 (X = 21.30..81.30)
    for kx in CARDKB_COL_XS_11:
        for r_idx in range(3):
            y_top = CARDKB_ROW_YS[r_idx]
            y_bot = CARDKB_ROW_YS[r_idx + 1]
            bridges.append(box_from_bounds(kx - 0.22, kx + 0.22, y_bot + 2.65, y_top - 2.65, 2.90, 3.16))
    # Vertical bridge between Row 0 and Row 1 at Column 0 (X = 15.30)
    bridges.append(box_from_bounds(15.30 - 0.22, 15.30 + 0.22, CARDKB_ROW_YS[1] + 2.65, CARDKB_ROW_YS[0] - 2.65, 2.90, 3.16))

    # Bridges connecting the 4 D-pad buttons into the array
    # Connect D-pad RIGHT (15.10, 10.20) to Row 3 Col 1 (21.30, 6.70) & D-pad UP (9.45, 14.95)
    bridges.append(box_from_bounds(15.10 - 0.22, 15.10 + 0.22, 10.20 + 2.15, 14.95, 2.90, 3.16))
    bridges.append(box_from_bounds(9.45 + 2.35, 15.32, 14.95 - 0.22, 14.95 + 0.22, 2.90, 3.16))
    bridges.append(box_from_bounds(15.10, 21.30 - 2.55, 6.70 - 0.22, 6.70 + 0.22, 2.90, 3.16))
    bridges.append(box_from_bounds(15.10 - 0.22, 15.10 + 0.22, 6.48, 10.20 - 2.15, 2.90, 3.16))
    # Central cross ring linking UP, DOWN, LEFT, RIGHT of D-pad
    bridges.append(box_from_bounds(3.80 + 2.35, 15.10 - 2.35, 10.20 - 0.25, 10.20 + 0.25, 2.90, 3.16))
    bridges.append(box_from_bounds(9.45 - 0.25, 9.45 + 0.25, 5.45 + 2.15, 14.95 - 2.15, 2.90, 3.16))

    res = trimesh.boolean.union([loose] + bridges, engine="manifold")
    res.merge_vertices()
    return res


# ---------------------------------------------------------------------------
# 3. Bezel Legend Text Solid & Bezel Cutout Helpers (in Local PCB Coordinates)
# ---------------------------------------------------------------------------
_CACHED_LEGEND_SOLIDS: dict[str, trimesh.Trimesh] = {}


def build_kb_bezel_legends_ams() -> trimesh.Trimesh:
    """
    Build the 3D extruded character legend bodies (Z_pcb = 5.95..6.40 mm) positioned on the
    4 horizontal bezel bars directly above each button row (plus D-pad symbols).
    Used both to deboss the bezel bars and as an optional multi-color AMS inlay STL.
    """
    if "pcb_legends" in _CACHED_LEGEND_SOLIDS:
        return _CACHED_LEGEND_SOLIDS["pcb_legends"].copy()

    from build123d import BuildSketch, Locations, Text, FontStyle, extrude, export_stl

    with BuildSketch() as sk:
        for r_idx, ry in enumerate(CARDKB_ROW_YS):
            xs = CARDKB_COL_XS_12 if r_idx < 2 else CARDKB_COL_XS_11
            lbl_y = ry + 4.85  # Centered on the horizontal bezel bar above each button row
            for c_idx, kx in enumerate(xs):
                txt = ROW_LEGENDS[r_idx][c_idx]
                fsize = 2.35 if len(txt) == 1 else 1.75
                with Locations((kx, lbl_y)):
                    Text(txt, font_size=fsize, font_style=FontStyle.BOLD)

    part = extrude(sk.sketch, amount=0.50)
    with tempfile.NamedTemporaryFile(suffix=".stl", delete=False) as tf:
        tmp_path = tf.name
    try:
        export_stl(part, tmp_path, tolerance=0.02, angular_tolerance=0.30)
        m = trimesh.load(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    # Position at Z_pcb = 5.95..6.45 mm (top of bezel is Z_pcb = 6.40 mm -> 0.45 mm deboss depth)
    m.apply_translation([0.0, 0.0, 5.95])
    m.merge_vertices()
    _CACHED_LEGEND_SOLIDS["pcb_legends"] = m
    return m.copy()


def _build_bezel_internal_cutouts_pcb() -> trimesh.Trimesh:
    """
    Build the combined internal cutout volume for any Top Bezel in Local PCB Coordinates:
      1. 50 vertical button shaft guide windows (Z_pcb = 3.55..6.50 mm)
      2. 50 underside flange counterbore pockets + flex-bridge channels (Z_pcb = 2.75..3.60 mm)
      3. Underside TPU mat membrane & registration pad clearance pockets (Z_pcb = -0.10..3.20 mm)
      4. Onboard RGB Status LED pinhole window (Ø1.80 mm at X=15.55, Y=21.32)
      5. Recessed horizontal bezel legend bar grooves (Z_pcb = 6.20..6.45 mm) + debossed character legends (Z_pcb = 5.95..6.45 mm)
    """
    cuts = []
    cl = CARDKB_BEZEL_CLEARANCE  # 0.20 mm radial clearance per side

    # 1 & 2. 50 Button guide holes (Z_pcb = 3.55..6.55) + Underside flange counterbores (Z_pcb = 2.75..3.60)
    for kx, ky, is_dpad in get_all_50_switch_centers():
        sw = (CARDKB_DPAD_SHAFT_W if is_dpad else CARDKB_KEY_SHAFT_W) + 2.0 * cl
        sh = (CARDKB_DPAD_SHAFT_H if is_dpad else CARDKB_KEY_SHAFT_H) + 2.0 * cl
        fw = (CARDKB_DPAD_FLANGE_W if is_dpad else CARDKB_KEY_FLANGE_W) + 0.45
        fh = (CARDKB_DPAD_FLANGE_H if is_dpad else CARDKB_KEY_FLANGE_H) + 0.45

        # Through shaft guide hole
        cuts.append(rounded_box_z(kx, ky, sw, sh, 3.50, 6.60, radius=0.65, sections=20))
        # Underside flange counterbore pocket (captures flange at Z_pcb = 2.90..3.50 with 0.10mm clearance)
        cuts.append(rounded_box_z(kx, ky, fw, fh, 2.75, 3.60, radius=0.80, sections=20))

    # Bridge clearance channels on underside of bezel (Z_pcb = 2.75..3.30) so 1-piece bridged tray seats flush
    for r_idx, ry in enumerate(CARDKB_ROW_YS):
        xs = CARDKB_COL_XS_12 if r_idx < 2 else CARDKB_COL_XS_11
        cuts.append(box_from_bounds(xs[0] - 2.0, xs[-1] + 2.0, ry - 0.55, ry + 0.55, 2.75, 3.30))
    for kx in CARDKB_COL_XS_12:
        cuts.append(box_from_bounds(kx - 0.55, kx + 0.55, CARDKB_ROW_YS[-1] - 1.0, CARDKB_ROW_YS[0] + 1.0, 2.75, 3.30))
    # D-pad bridge clearance pocket
    cuts.append(box_from_bounds(2.50, 22.00, 4.00, 16.50, 2.75, 3.30))

    # 3. Underside pocket for Continuous TPU Base Mat (84.0 x 54.0 mm, Z_pcb = -0.20..2.85 mm)
    cuts.append(box_from_bounds(-0.10, CARDKB_PCB_W + 0.10, -0.10, CARDKB_PCB_H + 0.10, -0.20, 2.85))

    # 4. Onboard RGB Status LED Pinhole (Ø1.80 mm through bezel at X=15.55, Y=21.32)
    led_x, led_y = CARDKB_RGB_LED_XY
    cuts.append(cylinder_z(led_x, led_y, 2.50, 6.60, radius=0.90, sections=24))

    # 5. Debossed 3D character legends on the horizontal bezel bars above each row (Z_pcb = 5.95..6.45 mm)
    cuts.append(build_kb_bezel_legends_ams())

    return trimesh.boolean.union(cuts, engine="manifold")


# ---------------------------------------------------------------------------
# 4. MeshSlide SlideKB_Pro Top Bezel (KB_S1_Pro) & Ultra-Slim Backplate (KB_S3_Pro)
# ---------------------------------------------------------------------------
def build_kb_s1_pro() -> trimesh.Trimesh:
    """
    Build the MeshSlide-compatible Top Bezel (`KB_S1_Pro`, 68.00 x 7.00 x 96.50 mm):
      - Preserves 100% of the outer perimeter, M2 corner bosses, top slide-rail interface, and side snap tabs
        of `STL/Expansion_Modules/KB_S1.STL`.
      - Closes the open window (and removes the Grove connector cutout) with a solid rigid top bezel plate
        featuring 50 back-loaded button guide windows, underside flange pockets, RGB LED pinhole, and
        debossed bezel-bar character legends.
      - Includes an internal concealed wire passage from the CardKB top-left solder pads into the top rail.
    """
    orig_s1 = trimesh.load(os.path.join(REF_STL_DIR, "KB_S1.STL"))

    # Fill the open front bezel window across the PCB area (X_S1 = 10.0..65.2, Z_S1 = 5.5..90.5, Y_S1 = 3.40..7.00)
    bezel_slab = box_from_bounds(10.00, 65.20, 3.40, 7.00, 5.50, 90.50)
    # Preserve the 2 bottom corner M2 screw counterbores at (X=54.5, Z=3.5) and (X=54.5, Z=93.0)
    filled_s1 = trimesh.boolean.union([orig_s1, bezel_slab], engine="manifold")

    # Transform the PCB-frame bezel cutouts into KB_S1_Pro coordinates
    pcb_cuts = _build_bezel_internal_cutouts_pcb()
    s1_cuts = pcb_to_s1_transform(pcb_cuts)

    # Add internal concealed wire channel from top-left CardKB solder pads (X_S1=10.8..16.0, Z_S1=80.0..88.5)
    # up towards the top pogo rail cavity (X_S1=5.0..12.0, Z_S1=60.0..88.5, Y_S1=-0.1..3.45)
    wire_ch_s1 = box_from_bounds(5.50, 15.00, -0.10, 3.45, 62.00, 88.50)

    res = trimesh.boolean.difference([filled_s1, s1_cuts, wire_ch_s1], engine="manifold")
    res.merge_vertices()
    return res


def build_kb_s3_pro() -> trimesh.Trimesh:
    """
    Build the MeshSlide-compatible Ultra-Slim Backplate (`KB_S3_Pro`):
      - Starts from `STL/Expansion_Modules/KB_S3.STL` (71.80 x 7.00 x 96.50 mm).
      - Preserves 100% of the top pogo-pin & slide-rail boss (X_S3 = 0.0..18.5 mm, Y_S3 = 0.0..7.0 mm),
        perimeter mating rim, 4x M2 screw holes, side snap tabs, and Ø4.6mm Lego alignment boss.
      - Eliminates the bulky 4.40 mm rear Grove connector bulge over the keyboard area (X_S3 = 18.5..71.8 mm),
        slimming the rear keyboard backplate down to Y_S3 = 2.60 mm with a smooth chamfer transition.
      - Adds a concealed internal wire raceway routing the 4 direct-soldered I2C wires from the CardKB pads
        straight into the central KB_M1 8-pin magnetic pogo cavity.
    """
    orig_s3 = trimesh.load(os.path.join(REF_STL_DIR, "KB_S3.STL"))

    # 1. Add a solid slim back wall at Y_S3 = 1.00..2.60 mm across the keyboard cavity (X_S3 = 14.5..70.0, Z_S3 = 2.1..94.4)
    #    so when we trim off Y_S3 > 2.60 mm (for X_S3 > 18.5), the back of the keyboard is a solid 1.60 mm flat plate!
    slim_back_plate = box_from_bounds(14.50, 70.00, 1.00, 2.60, 2.10, 94.40)
    # Keep the bottom-left and bottom-right M2 screw holes at (X_S3 = 58.30, Z_S3 = 3.50 and 93.00) open!
    m2_holes_bot = [
        cylinder_y_s3(58.30, 3.50, -0.5, 8.0, radius=1.15),
        cylinder_y_s3(58.30, 93.00, -0.5, 8.0, radius=1.15),
    ]
    # Keep the Lego hole counterbore through-hole at (X_S3 = 21.60, Z_S3 = 13.40) clear
    lego_hole_s3 = cylinder_y_s3(21.60, 13.40, -0.5, 8.0, radius=1.20)

    s3_with_plate = trimesh.boolean.union([orig_s3, slim_back_plate], engine="manifold")

    # 2. Trim off the rear Grove connector bulge (Y_S3 > 2.60 mm for X_S3 > 18.50 mm, with a 45-deg chamfer from X=14.1..18.5)
    trim_pts = np.array([
        [14.10, 7.10, -1.0], [75.00, 7.10, -1.0], [75.00, 2.60, -1.0], [18.50, 2.60, -1.0],
        [14.10, 7.10, 98.0], [75.00, 7.10, 98.0], [75.00, 2.60, 98.0], [18.50, 2.60, 98.0],
    ], dtype=float)
    rear_trim = trimesh.convex.convex_hull(trim_pts)

    # 3. Carve concealed internal wire channel from top-left solder pads (Z_S3 = 8.0..20.0, X_S3 = 14.0..20.0)
    #    diagonally/horizontally into the central KB_M1 pogo opening (Z_S3 = 32.5..64.0, X_S3 = 9.0..19.0, Y_S3 = -0.1..1.8)
    wire_raceway = box_from_bounds(11.00, 18.20, -0.10, 1.80, 8.00, 35.00)
    solder_pad_relief = box_from_bounds(14.50, 26.00, -0.10, 1.60, 6.50, 11.50)

    # Ensure clean 84.20 x 54.20 mm PCB pocket clearance on Y_S3 = 0.00..1.00 mm while preserving the Ø4.6mm Lego pin at (21.60, 13.40)
    pcb_pocket_trim = box_from_bounds(14.60, 68.85, -0.10, 1.00, 6.35, 90.65)
    lego_pin_guard = cylinder_y_s3(21.60, 13.40, -0.20, 1.10, radius=2.30)
    pcb_pocket_trim = trimesh.boolean.difference([pcb_pocket_trim, lego_pin_guard], engine="manifold")

    cuts = trimesh.boolean.union(
        [rear_trim, wire_raceway, solder_pad_relief, pcb_pocket_trim, lego_hole_s3] + m2_holes_bot, engine="manifold"
    )
    res = trimesh.boolean.difference([s3_with_plate, cuts], engine="manifold")
    res.merge_vertices()
    return res


def cylinder_y_s3(x: float, z: float, ymin: float, ymax: float, radius: float, sections: int = 32) -> trimesh.Trimesh:
    c = trimesh.creation.cylinder(radius=radius, height=(ymax - ymin), sections=sections)
    R = trimesh.transformations.rotation_matrix(math.pi / 2.0, [1, 0, 0])
    c.apply_transform(R)
    c.apply_translation([x, (ymin + ymax) / 2.0, z])
    return c


# ---------------------------------------------------------------------------
# 5. Standalone Ultra-Slim CardKB Pro Enclosure (Bezel + Backplate)
# ---------------------------------------------------------------------------
STANDALONE_PAD_X = 4.00  # 4.00 mm left/right border around 84.0 mm PCB -> 92.00 mm width (matches Printables #1512657)
STANDALONE_PAD_Y = 3.00  # 3.00 mm top/bottom border around 54.0 mm PCB -> 60.00 mm height
STANDALONE_SCREWS_XY = [
    (-2.00, 49.00),
    (86.00, 49.00),
    (-2.00,  5.00),
    (86.00,  5.00),
]


def build_cardkb_standalone_bezel() -> trimesh.Trimesh:
    """
    Build the Standalone Ultra-Slim Top Bezel (`CardKB_Standalone_Bezel`, 92.00 x 60.00 x 6.40 mm):
      - Spans X_pcb in [-4.0..88.0], Y_pcb in [-3.0..57.0], Z_pcb in [0.00..6.40 mm].
      - Uses the exact same 50 button guide windows, underside flange pockets, TPU mat seat,
        RGB LED pinhole, and debossed bezel-bar legends as KB_S1_Pro.
      - Includes 4x M2 side-border mounting holes completely outside the 84x54mm PCB/TPU pocket.
    """
    w = CARDKB_PCB_W + 2.0 * STANDALONE_PAD_X  # 92.00 mm
    h = CARDKB_PCB_H + 2.0 * STANDALONE_PAD_Y  # 60.00 mm
    xc = CARDKB_PCB_W / 2.0
    yc = CARDKB_PCB_H / 2.0

    outer = rounded_box_z(xc, yc, w, h, 0.00, 6.40, radius=3.00, sections=32)

    screw_holes = [cylinder_z(sx, sy, -0.20, 4.80, radius=0.95, sections=28) for sx, sy in STANDALONE_SCREWS_XY]
    pcb_cuts = _build_bezel_internal_cutouts_pcb()

    # Top-edge strain-relief wire exit notch at X_pcb in [2.5..8.0], Y_pcb in [53.5..57.5], Z_pcb in [0.0..2.2]
    wire_slot = box_from_bounds(2.50, 8.00, 53.50, 57.50, -0.10, 2.20)

    all_cuts = trimesh.boolean.union([pcb_cuts, wire_slot] + screw_holes, engine="manifold")
    res = trimesh.boolean.difference([outer, all_cuts], engine="manifold")
    # Shift to positive quadrant [0..92.0, 0..60.0, 0..6.4]
    bmin = res.bounds[0]
    res.apply_translation([-bmin[0], -bmin[1], -bmin[2]])
    res.merge_vertices()
    return res


def build_cardkb_standalone_back() -> trimesh.Trimesh:
    """
    Build the Standalone Ultra-Slim Backplate (`CardKB_Standalone_Back`, 92.00 x 60.00 x 2.80 mm):
      - Spans Z_pcb = -2.80 to 0.00 mm (1.20 mm solid flat rear wall + 1.60 mm perimeter cradle for the 1.60 mm PCB).
      - Includes 2x Ø4.60 mm Lego registration pins at (6.90, 37.10) and (6.19, 49.51) that lock into the CardKB PCB.
      - Includes 4x M2 countersunk through-holes and a top-edge wire strain-relief channel.
    """
    w = CARDKB_PCB_W + 2.0 * STANDALONE_PAD_X  # 92.00 mm
    h = CARDKB_PCB_H + 2.0 * STANDALONE_PAD_Y  # 60.00 mm
    xc = CARDKB_PCB_W / 2.0
    yc = CARDKB_PCB_H / 2.0

    outer = rounded_box_z(xc, yc, w, h, -2.80, 0.00, radius=3.00, sections=32)

    # 84.20 x 54.20 x 1.60 mm PCB cradle pocket (Z_pcb = -1.60..0.10 mm)
    pcb_pocket = box_from_bounds(-0.10, CARDKB_PCB_W + 0.10, -0.10, CARDKB_PCB_H + 0.10, -1.60, 0.10)

    # Top-edge strain-relief wire channel (X_pcb in [2.5..8.0], Y_pcb in [50.0..57.5], Z_pcb in [-1.60..0.10])
    wire_slot = box_from_bounds(2.50, 8.00, 50.00, 57.50, -1.60, 0.10)

    # 4x M2 through-holes + rear counterbores
    screw_cuts = []
    for sx, sy in STANDALONE_SCREWS_XY:
        screw_cuts.append(cylinder_z(sx, sy, -3.00, 0.50, radius=1.10, sections=28))
        screw_cuts.append(cylinder_z(sx, sy, -3.00, -1.80, radius=1.85, sections=28))

    carved = trimesh.boolean.difference(
        [outer, trimesh.boolean.union([pcb_pocket, wire_slot] + screw_cuts, engine="manifold")],
        engine="manifold",
    )

    # Add 2x Ø4.60 mm Lego registration pins protruding from the floor through the 1.60 mm PCB (Z_pcb = -1.60..0.00 mm)
    lego_pins = [
        cylinder_z(CARDKB_LEGO_LOWER_XY[0], CARDKB_LEGO_LOWER_XY[1], -1.60, 0.00, radius=2.30, sections=32),
        cylinder_z(CARDKB_LEGO_UPPER_XY[0], CARDKB_LEGO_UPPER_XY[1], -1.60, 0.00, radius=2.30, sections=32),
    ]
    res = trimesh.boolean.union([carved] + lego_pins, engine="manifold")
    bmin = res.bounds[0]
    res.apply_translation([-bmin[0], -bmin[1], -bmin[2]])
    res.merge_vertices()
    return res
