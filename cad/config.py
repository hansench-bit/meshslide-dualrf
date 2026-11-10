"""
Parametric configuration and CSG geometry utilities for MeshSlide-DualRF.
Supports both RAK WisBlock (RAK19007 + RAK4631 + RAK12500 + 0.96" OLED)
and Seeed Studio Wio Tracker L1 (1.3" OLED + 4-way Joystick + Menu Button),
with top-mounted vertical N-Type (915 MHz) and SMA (GPS) bulkheads,
Rokland PID 920452 JST-PH inline slide switch pocket, +10mm body height,
and +4mm deep battery compartment while preserving 100% Slide-module compatibility.
"""

from __future__ import annotations
import os
import math
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
import trimesh

# ---------------------------------------------------------------------------
# Release Versioning & Workspace Paths
# ---------------------------------------------------------------------------
MODEL_VERSION = "v2.0"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REF_STL_DIR = os.path.join(ROOT_DIR, "reference_original")
OUT_STL_DIR = os.path.join(ROOT_DIR, "STL")
OUT_STEP_DIR = os.path.join(ROOT_DIR, "STEP")
OUT_3MF_DIR = os.path.join(ROOT_DIR, "3MF")
OUT_SCAD_DIR = os.path.join(ROOT_DIR, "OpenSCAD")
OUT_RENDER_DIR = os.path.join(ROOT_DIR, "renders")

# ---------------------------------------------------------------------------
# Global Enclosure Dimensions (mm)
# ---------------------------------------------------------------------------
CASE_LENGTH = 96.50
BASE_BODY_WIDTH = 18.00        # Standard MeshSlide thickness at top/bottom rails
ORIG_BODY_HEIGHT = 35.00       # Original CaseU1 / CaseL1 height
ORIG_MIDFRAME_HEIGHT = 37.00   # Original CaseM1 height
HEIGHT_EXPANSION = 10.00       # +10.0 mm vertical expansion for 30mm RAK19007 PCB
BODY_HEIGHT = ORIG_BODY_HEIGHT + HEIGHT_EXPANSION           # 45.00 mm (RAK)
MIDFRAME_HEIGHT = ORIG_MIDFRAME_HEIGHT + HEIGHT_EXPANSION   # 47.00 mm (RAK)

WIO_HEIGHT_EXPANSION = 38.00   # +38.0 mm vertical expansion for 48.06 x 52.00 mm Wio Tracker L1 PCB + 10.5mm lower Grove plug bay
WIO_BODY_HEIGHT = ORIG_BODY_HEIGHT + WIO_HEIGHT_EXPANSION           # 73.00 mm (Wio Tracker L1)
WIO_MIDFRAME_HEIGHT = ORIG_MIDFRAME_HEIGHT + WIO_HEIGHT_EXPANSION   # 75.00 mm (Wio Tracker L1)

# Z-plane in original CaseM1 coordinates (0=Top, 37=Bottom) where the +10mm stretch is applied.
# Z=24.0 is cleanly below CaseS1's right mounting leg (Z=21.0) and above CaseR1's collar (Z=31.0).
STRETCH_SPLIT_Z_M1 = 24.00
STRETCH_SPLIT_Z_L1 = 22.00     # Since Z_L1 = Z_M1 - 2.0

# ---------------------------------------------------------------------------
# RF Bulkhead Specifications (CaseS1_DualRF & CaseS1_DualRF_BoltOn)
# ---------------------------------------------------------------------------
# 1. N-Type Female Bulkhead (5/8"-24 UNEF thread, 16mm mounting hole with D-flat)
# Shifted left to X=68.50 mm (away from the X=88.5..96.5 right M2 screw leg) and raised to Z=-8.50 mm
# with an unobstructed Ø24.60 mm bottom-entry pocket (Z=-5.70 down through bottom) so the Ø23.0 mm
# rear flange + red O-ring pushes straight up from the bottom and seats above the 18mm case walls!
N_TYPE_X = 73.50               # Center X on CaseS1 top rail (shifted into open right-side RF bay)
N_TYPE_Y = 9.00                # Centered in Y (18.0 / 2)
N_TYPE_HOLE_DIA = 16.30        # 16.0mm nominal + 0.3mm FDM tolerance
N_TYPE_D_FLAT = 15.15          # Anti-rotation flat width (15.0mm nominal + 0.15mm clearance)
N_TYPE_BOSS_OD = 28.60         # Reinforced top turret outer diameter (2.0mm wall around Ø24.6mm flange pocket)
N_TYPE_NUT_CLEAR_DIA = 24.60   # Unobstructed bottom-loading pocket for Ø23.0mm silver flange + red O-ring
N_TYPE_DECK_Z_TOP = -10.00     # Raised turret deck 10.0mm above Z=0 so straight coax ferrule clears PCB
N_TYPE_FLANGE_THICK = 2.80     # Bulkhead top wall thickness (leaves ~12.9mm of protruding 5/8"-24 thread)

# 1b. Bolt-On 4-Hole Square Flange N-Type Female Mount (25x25mm / UG-58A/U flange, 18.30mm grid, M3 captive nuts)
N_TYPE_BOLT_FLANGE_X = 27.40   # 27.4 mm pad width in X (1.2mm wall around 4x M3 hex nut sockets)
N_TYPE_BOLT_FLANGE_Y = 26.80   # 26.8 mm pad width in Y (Y = -4.40..+22.40 mm)
N_TYPE_BOLT_GRID = 18.30       # 18.30 x 18.30 mm center-to-center (15.0 mm inside edge-to-edge + 3.3 mm hole)
N_TYPE_BOLT_CENTER_DIA = 10.60 # Center through-bore for rear PTFE/coax barrel of 4-bolt N-Type connector
N_TYPE_BOLT_HOLE_DIA = 3.40    # 4x Ø3.40 mm M3 clearance holes
N_TYPE_BOLT_NUT_AF = 5.75      # Captive M3 hex nut socket width across flats (5.50 mm nut + 0.25 mm clearance)

# 2. SMA Female Bulkhead for GPS (1/4"-36 UNS thread, 6.5mm hole with D-flat + 8mm hex trap)
SMA_X = 54.00                  # Shifted right to X=54.00 mm (clear of Wio PCB right edge at X=50.28 mm)
SMA_Y = 9.00                   # Centered in Y
SMA_HOLE_DIA = 6.55            # 6.35mm nominal + FDM clearance
SMA_D_FLAT = 6.05              # Anti-rotation D-flat width
SMA_HEX_AF = 8.25              # 8.0mm hex nut + 0.25mm clearance across flats
SMA_BOSS_OD = 15.00            # Reinforced collar around SMA mount
SMA_FLANGE_THICK = 2.80        # Top wall thickness for SMA thread engagement

# ---------------------------------------------------------------------------
# Battery & Rokland Inline Power Switch Specifications (CaseL1_Deep & CaseM1)
# ---------------------------------------------------------------------------
BATTERY_EXTRA_DEPTH = 6.60     # +6.6mm outward expansion on CaseL1 (11.0mm clear internal battery depth for 10mm packs)
BATTERY_MAX_DIMS = (82.0, 34.0, 10.0)  # Fits 103450 / 103665 2000-3000mAh LiPo pouches

# Rokland PID 920452 (RAK Wireless 2-Pin JST-PH 2.0 Battery Cable with Power Switch)
ROKLAND_SW_Z_CENTER = 33.50    # Center Z (in expanded M1 coords) on left wall (X=0) below USB-C
ROKLAND_SW_BODY_L = 9.00       # Switch body length (Z) + clearance
ROKLAND_SW_BODY_W = 4.30       # Switch body width (Y) + clearance
ROKLAND_SW_BODY_D = 4.60       # Switch body depth (X) into left wall
ROKLAND_SW_SLOT_L = 5.60       # External actuator slider slot length (Z)
ROKLAND_SW_SLOT_W = 2.80       # External actuator slider slot width (Y)

# ---------------------------------------------------------------------------
# Board Platform A: RAK WisBlock (RAK19007 + RAK4631 + RAK12500 + 0.96" OLED)
# ---------------------------------------------------------------------------
RAK_PCB_L = 60.40              # 60.0mm + 0.4mm pocket clearance
RAK_PCB_W = 30.40              # 30.0mm + 0.4mm pocket clearance
RAK_PCB_X0 = 2.00              # Left edge at X=2.0mm (USB-C protrudes to X=0.0mm)
RAK_PCB_Z0 = 6.50              # Top edge at Z=6.5mm in expanded M1 (Z=6.5..36.9mm)
RAK_HOLE_DX = 55.20            # Corner M2 hole spacing X
RAK_HOLE_DZ = 25.20            # Corner M2 hole spacing Z
RAK_OLED_WIN_W = 25.00         # 0.96" OLED active window width (X)
RAK_OLED_WIN_H = 14.50         # 0.96" OLED active window height (Z)
RAK_OLED_PCB_W = 28.20         # RAK1921 / SSD1306 module width
RAK_OLED_PCB_H = 27.80         # RAK1921 / SSD1306 module height
RAK_OLED_CENTER_X = 35.00      # Window center X in assembly coords
RAK_OLED_CENTER_Z = 21.50      # Window center Z in expanded assembly coords

# ---------------------------------------------------------------------------
# Board Platform B: Seeed Studio Wio Tracker L1 (Official 48.06 x 52.00 mm PCB)
# ---------------------------------------------------------------------------
# Extracted directly from Seeed Studio's official Wio_Tracker_L1_outline.dxf & L1pro_3D_Enclosure.stp:
# - Bare PCB is 48.06 mm wide (X) x 52.00 mm tall (Z), with 4x corner M2 holes on a 43.06 x 47.00 mm grid
# - Upper half of front face: 1.3" OLED (centered at X_pcb = 0.00, Z_pcb = -16.00) + 24P E-Ink header (right)
# - Lower-right of front face: Menu button (X_pcb = +6.93, Z_pcb = +8.30) + 4-Way Joystick (X_pcb = +18.03, Z_pcb = +8.30)
# - Bottom edge of front face: Grove I2C socket (X_pcb = +7.20..+20.36) + Solar 2P socket (X_pcb = -17.97..-10.75)
# - Left edge (X_pcb = -24.03): RST (Z_pcb = -15.90), Power switch (Z_pcb = -6.00), USB-C (Z_pcb = +7.80)
WIO_PCB_L = 48.50              # 48.06mm + 0.44mm pocket clearance (X = 2.00..50.50 mm, center XC = 26.25 mm)
WIO_PCB_W = 52.40              # 52.00mm + 0.40mm pocket clearance (Z_M1 = 6.80..59.20 mm, center ZC = 33.00 mm)
WIO_PCB_X0 = 2.00              # Left edge at X=2.0mm (USB-C / Power Switch / RST on left edge X=0)
WIO_PCB_Z0 = 6.80              # Top edge at Z=6.8mm in expanded M1 (below top-left M2 screw boss)
WIO_HOLE_DX = 43.06            # Official 4x corner M2 mounting holes X spacing (±21.53 mm)
WIO_HOLE_DZ = 47.00            # Official 4x corner M2 mounting holes Z spacing (±23.50 mm)
WIO_OLED_WIN_W = 30.00         # 1.3" OLED active viewing window width (X) centered over active glass (left of E-Ink FPC)
WIO_OLED_WIN_H = 15.50         # 1.3" OLED active viewing window height (Z)
WIO_OLED_CENTER_X = 25.05      # 1.3" OLED active glass center X (XC - 1.20 mm)
WIO_OLED_CENTER_Z = 16.20      # 1.3" OLED center Z in expanded M1 coords (Z_U1 = 14.20 mm)
WIO_JOY_CENTER_X = 44.28       # Official 4-way joystick center X (XC + 18.03 mm from wio_tracker_l1_pro_qian-3d.stp)
WIO_JOY_CENTER_Z = 41.30       # Official 4-way joystick center Z in M1 coords (ZC + 8.30 mm -> Z_U1 = 39.30 mm)
WIO_JOY_HOLE_DIA = 7.50        # Official Seeed bezel inner bore Ø7.50 mm expanding to Ø8.20 mm conical bevel
WIO_BTN_CENTER_X = 33.18       # Official Menu button center X (XC + 6.93 mm from wio_tracker_l1_pro_qian-3d.stp)
WIO_BTN_CENTER_Z = 41.30       # Official Menu button center Z in M1 coords (ZC + 8.30 mm -> Z_U1 = 39.30 mm)

# ---------------------------------------------------------------------------
# CardKB Pro Hybrid Enclosure Specifications (Back-Loaded PETG/PLA + TPU Mat)
# ---------------------------------------------------------------------------
# Bare FR4 PCB is 84.00 x 54.00 x 1.60 mm (88.0mm nominal includes protruding Grove port, removed here)
CARDKB_PCB_W = 84.00
CARDKB_PCB_H = 54.00
CARDKB_PCB_T = 1.60
CARDKB_SMD_SW_H = 1.40

# In KB_S1_Pro coordinates (X_S1 in [0..68.0] top-to-bottom, Z_S1 in [0..96.5] right-to-left, Y_S1 in [0..7.0] back-to-front):
# PCB pocket spans X_S1 = 10.80..65.00 (54.20mm), Z_S1 = 5.90..90.10 (84.20mm)
CARDKB_S1_PCB_X0 = 10.90       # Top edge of 54.0mm PCB in KB_S1 coords
CARDKB_S1_PCB_Z0 = 90.00       # Left edge of 84.0mm PCB in KB_S1 coords (since +Z is left when viewing front Y=7.0)

# 50 Switch Matrix in CardKB Local PCB Coordinates (X_pcb in [0..84.0] Left->Right, Y_pcb in [0..54.0] Bottom->Top):
CARDKB_COL_XS_12 = [15.30 + c * 6.00 for c in range(12)]   # Cols 0..11 (15.30 to 81.30 mm)
CARDKB_COL_XS_11 = [21.30 + c * 6.00 for c in range(11)]   # Cols 1..11 (21.30 to 81.30 mm)
CARDKB_ROW_YS = [42.70, 30.70, 18.70, 6.70]                # Rows 0..3 (Top to Bottom, 12.00mm pitch)

# 4-Way D-Pad Switch Centers in Local PCB Coordinates (X_pcb, Y_pcb):
CARDKB_DPAD_UP = (9.45, 14.95)
CARDKB_DPAD_DOWN = (9.45, 5.45)
CARDKB_DPAD_LEFT = (3.80, 10.20)
CARDKB_DPAD_RIGHT = (15.10, 10.20)

# Onboard RGB Status LED & Lego Registration Holes in Local PCB Coordinates (X_pcb, Y_pcb):
CARDKB_RGB_LED_XY = (15.55, 21.32)
CARDKB_LEGO_LOWER_XY = (6.90, 47.10)   # Matches KB_S3 boss at Z_S3=13.40 (Z_S1=83.10), X_S3=21.60 (X_S1=17.80 -> Y_pcb=47.10)
CARDKB_LEGO_UPPER_XY = (6.90, 29.10)   # Second Lego hole 18.0mm below top-left Lego hole

# Keycap, Bezel, and TPU Mat Stackup Dimensions (mm):
CARDKB_KEY_SHAFT_W = 4.30
CARDKB_KEY_SHAFT_H = 4.60
CARDKB_BEZEL_CLEARANCE = 0.20          # 0.20mm per side -> 4.70 x 5.00 mm guide window
CARDKB_KEY_FLANGE_W = 5.40
CARDKB_KEY_FLANGE_H = 5.70
CARDKB_KEY_FLANGE_T = 0.60
CARDKB_DPAD_SHAFT_W = 4.00
CARDKB_DPAD_SHAFT_H = 3.60
CARDKB_DPAD_FLANGE_W = 5.00
CARDKB_DPAD_FLANGE_H = 4.60
CARDKB_TPU_MEMBRANE_T = 0.70
CARDKB_TPU_PLUNGER_DIA = 2.60



# ---------------------------------------------------------------------------
# CSG Primitive & Mesh Manipulation Helpers (using trimesh + manifold3d)
# ---------------------------------------------------------------------------
def box_from_bounds(xmin: float, xmax: float, ymin: float, ymax: float, zmin: float, zmax: float) -> trimesh.Trimesh:
    """Create an axis-aligned box mesh spanning exact [xmin..xmax, ymin..ymax, zmin..zmax]."""
    size = [xmax - xmin, ymax - ymin, zmax - zmin]
    center = [(xmin + xmax) / 2.0, (ymin + ymax) / 2.0, (zmin + zmax) / 2.0]
    b = trimesh.creation.box(extents=size)
    b.apply_translation(center)
    return b


def cylinder_z(x: float, y: float, zmin: float, zmax: float, radius: float, sections: int = 64) -> trimesh.Trimesh:
    """Create a vertical cylinder along the Z axis from zmin to zmax centered at (x, y)."""
    h = zmax - zmin
    c = trimesh.creation.cylinder(radius=radius, height=h, sections=sections)
    c.apply_translation([x, y, (zmin + zmax) / 2.0])
    return c


def cylinder_y(x: float, z: float, ymin: float, ymax: float, radius: float, sections: int = 48) -> trimesh.Trimesh:
    """Create a horizontal cylinder along the Y axis from ymin to ymax centered at (x, z)."""
    h = ymax - ymin
    c = trimesh.creation.cylinder(radius=radius, height=h, sections=sections)
    # Rotate Z axis to Y axis (90 deg around X)
    R = trimesh.transformations.rotation_matrix(math.pi / 2.0, [1, 0, 0])
    c.apply_transform(R)
    c.apply_translation([x, (ymin + ymax) / 2.0, z])
    return c


def d_hole_z(x: float, y: float, zmin: float, zmax: float, dia: float, d_flat_width: float, sections: int = 64) -> trimesh.Trimesh:
    """
    Create a vertical D-shaped mounting hole solid (for N-Type or SMA bulkhead anti-rotation).
    `dia` is the full circular diameter; `d_flat_width` is the distance from the opposite arc to the flat.
    """
    r = dia / 2.0
    cyl = cylinder_z(x, y, zmin, zmax, radius=r, sections=sections)
    # Cut off the top (+Y) edge beyond y - r + d_flat_width
    flat_y = (y - r) + d_flat_width
    clip_box = box_from_bounds(x - r - 1.0, x + r + 1.0, flat_y, y + r + 2.0, zmin - 1.0, zmax + 1.0)
    return trimesh.boolean.difference([cyl, clip_box], engine="manifold")


def hex_prism_z(x: float, y: float, zmin: float, zmax: float, across_flats: float) -> trimesh.Trimesh:
    """Create a vertical hexagonal nut trap prism centered at (x, y) with given width across flats."""
    circum_r = across_flats / math.sqrt(3.0)
    c = trimesh.creation.cylinder(radius=circum_r, height=(zmax - zmin), sections=6)
    c.apply_translation([x, y, (zmin + zmax) / 2.0])
    return c


def chamfered_window_y(
    xc: float, zc: float, w: float, h: float, ymin: float, ymax: float, bevel: float = 1.2
) -> trimesh.Trimesh:
    """
    Create a rectangular through-cutout along Y with a 45-degree front bezel chamfer at ymax.
    """
    core = box_from_bounds(xc - w / 2.0, xc + w / 2.0, ymin, ymax + 0.5, zc - h / 2.0, zc + h / 2.0)
    if bevel <= 0:
        return core
    # Build frustum for front bevel from (ymax - bevel) to (ymax + 0.1)
    z0, z1 = zc - h / 2.0, zc + h / 2.0
    x0, x1 = xc - w / 2.0, xc + w / 2.0
    b = bevel + 0.1
    y_in = ymax - bevel
    y_out = ymax + 0.1
    verts = np.array([
        [x0, y_in, z0], [x1, y_in, z0], [x1, y_in, z1], [x0, y_in, z1],
        [x0 - b, y_out, z0 - b], [x1 + b, y_out, z0 - b], [x1 + b, y_out, z1 + b], [x0 - b, y_out, z1 + b],
    ], dtype=float)
    hull = trimesh.convex.convex_hull(verts)
    return trimesh.boolean.union([core, hull], engine="manifold")


def stretch_mesh_z(mesh: trimesh.Trimesh, split_z: float, delta_z: float, slice_eps: float = 0.25) -> trimesh.Trimesh:
    """
    Stretch a mesh along the +Z axis by `delta_z` at `split_z` while preserving
    100% of the exact geometry above `split_z` and below `split_z`!
    """
    bmin, bmax = mesh.bounds
    pad = 10.0
    # 1. Top half: z <= split_z + slice_eps
    top_box = box_from_bounds(bmin[0] - pad, bmax[0] + pad, bmin[1] - pad, bmax[1] + pad, bmin[2] - pad, split_z + slice_eps)
    top_part = trimesh.boolean.intersection([mesh, top_box], engine="manifold")

    # 2. Bottom half: z >= split_z - slice_eps, shifted down by +delta_z
    bot_box = box_from_bounds(bmin[0] - pad, bmax[0] + pad, bmin[1] - pad, bmax[1] + pad, split_z - slice_eps, bmax[2] + pad)
    bot_part = trimesh.boolean.intersection([mesh, bot_box], engine="manifold")
    bot_part.apply_translation([0.0, 0.0, delta_z])

    # 3. Middle bridge: take thin slab [split_z - slice_eps, split_z + slice_eps] and scale it in Z to bridge [split_z, split_z + delta_z]
    slab_box = box_from_bounds(bmin[0] - pad, bmax[0] + pad, bmin[1] - pad, bmax[1] + pad, split_z - slice_eps, split_z + slice_eps)
    slab = trimesh.boolean.intersection([mesh, slab_box], engine="manifold")
    scale_z = (delta_z + 2.0 * slice_eps) / (2.0 * slice_eps)
    v = slab.vertices.copy()
    v[:, 2] = (v[:, 2] - split_z) * scale_z + split_z + (delta_z / 2.0)
    slab.vertices = v

    res = trimesh.boolean.union([top_part, slab, bot_part], engine="manifold")
    res.vertices = np.round(res.vertices.astype(np.float32), 4)
    rbmin, rbmax = res.bounds
    huge = box_from_bounds(rbmin[0] - 10.0, rbmax[0] + 10.0, rbmin[1] - 10.0, rbmax[1] + 10.0, rbmin[2] - 10.0, rbmax[2] + 10.0)
    return trimesh.boolean.intersection([res, huge], engine="manifold")


def export_step_ap214(mesh: trimesh.Trimesh, filepath: str, part_name: str = "MeshSlide_Part") -> None:
    """
    Export a watertight Trimesh solid to an ISO 10303-21 (STEP AP214) faceted B-Rep / shell model
    so CAD applications (Fusion 360, SolidWorks, FreeCAD, Bambu Studio, OrcaSlicer) can import it directly.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    verts = np.round(mesh.vertices, 4)
    faces = mesh.faces

    lines = [
        "ISO-10303-21;",
        "HEADER;",
        f"FILE_DESCRIPTION(('MeshSlide-DualRF {part_name}'),'2;1');",
        f"FILE_NAME('{os.path.basename(filepath)}','2026-10-30T12:00:00',('MeshSlide-DualRF'),('Antigravity CAD'),'','','');",
        "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));",
        "ENDSEC;",
        "DATA;",
        "#1=APPLICATION_CONTEXT('automotive design');",
        "#2=APPLICATION_PROTOCOL_DEFINITION('draft international standard','automotive_design',1998,#1);",
        f"#3=PRODUCT('{part_name}','{part_name}','',(#4));",
        "#4=PRODUCT_CONTEXT('',#1,'mechanical');",
        "#5=PRODUCT_DEFINITION_FORMATION_WITH_SPECIFIED_SOURCE('','',#3,.NOT_KNOWN.);",
        "#6=PRODUCT_DEFINITION('design','',#5,#7);",
        "#7=PRODUCT_DEFINITION_CONTEXT('part definition',#1,'design');",
        "#8=PRODUCT_DEFINITION_SHAPE('','',#6);",
        "#9=SHAPE_DEFINITION_REPRESENTATION(#8,#10);",
        "#10=MANIFOLD_SURFACE_SHAPE_REPRESENTATION('',(#11),#12);",
        "#12=(GEOMETRIC_REPRESENTATION_CONTEXT(3) GLOBAL_UNCERTAINTY_ASSIGNED_CONTEXT((#13)) GLOBAL_UNIT_ASSIGNED_CONTEXT((#14,#15,#16)) REPRESENTATION_CONTEXT('','3D'));",
        "#13=UNCERTAINTY_MEASURE_WITH_UNIT(LENGTH_MEASURE(1.E-04),#14,'distance_accuracy_value','');",
        "#14=(LENGTH_UNIT() NAMED_UNIT(*) SI_UNIT(.MILLI.,.METRE.));",
        "#15=(NAMED_UNIT(*) PLANE_ANGLE_UNIT() SI_UNIT($,.RADIAN.));",
        "#16=(NAMED_UNIT(*) SOLID_ANGLE_UNIT() SI_UNIT($,.STERADIAN.));",
    ]

    eid = 20
    pt_ids = []
    for vx, vy, vz in verts:
        lines.append(f"#{eid}=CARTESIAN_POINT('',({vx:.4f},{vy:.4f},{vz:.4f}));")
        pt_ids.append(eid)
        eid += 1

    face_ids = []
    for i0, i1, i2 in faces:
        p0, p1, p2 = pt_ids[i0], pt_ids[i1], pt_ids[i2]
        loop_id = eid
        bound_id = eid + 1
        face_id = eid + 2
        lines.append(f"#{loop_id}=POLY_LOOP('',(#{p0},#{p1},#{p2}));")
        lines.append(f"#{bound_id}=FACE_OUTER_BOUND('',#{loop_id},.T.);")
        lines.append(f"#{face_id}=FACE_SURFACE('',(#{bound_id}),#{p0},.T.);")
        face_ids.append(f"#{face_id}")
        eid += 3

    face_list_str = ",".join(face_ids)
    lines.append(f"#11=OPEN_SHELL('',({face_list_str}));")
    lines.append("ENDSEC;")
    lines.append("END-ISO-10303-21;")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
