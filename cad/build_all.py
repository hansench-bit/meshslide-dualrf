"""
Master build script for MeshSlide-DualRF.
Generates all STL, STEP, 3MF, OpenSCAD, and orthographic engineering renders
for both RAK19007 and Seeed Wio Tracker L1 configurations.
"""

from __future__ import annotations
import os
import sys
import subprocess
import numpy as np
import trimesh
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cad.config import (
    MODEL_VERSION,
    OUT_STL_DIR,
    OUT_STEP_DIR,
    OUT_3MF_DIR,
    OUT_SCAD_DIR,
    OUT_RENDER_DIR,
    export_step_ap214,
)
from cad.parts.case_s1_dual_rf import (
    build_case_s1_dual_rf,
    build_case_s1_dual_rf_bolton,
    build_case_s1_dual_rf_heatset,
)
from cad.parts.case_l1_deep import build_case_l1_deep, build_case_r1, build_case_slide
from cad.parts.tray_rak19007 import build_case_m1_rak, build_case_u1_rak, build_case_button
from cad.parts.tray_wio_l1 import (
    build_case_m1_wio_l1,
    build_case_u1_wio_l1,
    build_case_joystick_wio_l1,
    build_case_button_wio_l1,
)
from cad.parts.cardkb_pro import (
    pcb_to_s1_transform,
    build_kb_tpu_mat,
    build_kb_button_single,
    build_kb_buttons_loose_set,
    build_kb_buttons_bridged,
    build_kb_bezel_legends_ams,
    build_kb_s1_pro,
    build_kb_s3_pro,
    build_cardkb_standalone_bezel,
    build_cardkb_standalone_back,
)


def export_3mf_bundle(parts_dict: dict[str, trimesh.Trimesh], filepath: str) -> None:
    """Arrange parts neatly in a compact 2-column grid (oriented flat on Z=0) so all parts fit on a single build plate."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    scene = trimesh.Scene()
    cursor_x = 0.0
    cursor_y = 0.0
    row_max_y = 0.0
    R_pos90_x = trimesh.transformations.rotation_matrix(np.pi / 2.0, [1, 0, 0])
    R_neg90_x = trimesh.transformations.rotation_matrix(-np.pi / 2.0, [1, 0, 0])
    R_pos90_y = trimesh.transformations.rotation_matrix(np.pi / 2.0, [0, 1, 0])
    for name, m in parts_dict.items():
        mc = m.copy()
        if name.startswith("CaseU1"):
            mc.apply_transform(R_pos90_x)
        elif name.startswith("CaseM1") or name.startswith("CaseL1"):
            mc.apply_transform(R_neg90_x)
        elif name.startswith("CaseS1"):
            # Stand CaseS1 vertically on its completely flat X = 96.50 mm right end face (Z_print = 0)
            mc.apply_transform(R_pos90_y)
        bmin, bmax = mc.bounds
        w = bmax[0] - bmin[0]
        h = bmax[1] - bmin[1]
        if cursor_x > 0.0 and cursor_x + w > 215.0:
            cursor_x = 0.0
            cursor_y += row_max_y + 8.0
            row_max_y = 0.0
        mc.apply_translation([cursor_x - bmin[0], cursor_y - bmin[1], -bmin[2]])
        cursor_x += w + 10.0
        if h > row_max_y:
            row_max_y = h
        scene.add_geometry(mc, node_name=name, geom_name=name)
    scene.export(filepath, file_type="3mf")


def generate_openscad_customizer() -> None:
    """Write an OpenSCAD Customizer project file in OpenSCAD/ for easy user tweaking."""
    os.makedirs(OUT_SCAD_DIR, exist_ok=True)
    scad_path = os.path.join(OUT_SCAD_DIR, "MeshSlide_DualRF.scad")
    scad_code = """// ============================================================================
// MeshSlide-DualRF OpenSCAD Customizer & Assembly Viewer
// Supports:
//   1) RAK WisBlock (RAK19007 + RAK4631 + RAK12500 + 0.96" OLED)
//   2) Seeed Studio Wio Tracker L1 (1.3" OLED + 4-Way Joystick + Menu Button)
//   3) Top-Mounted Vertical N-Type (915 MHz) + Vertical SMA (GPS) Bulkheads
//   4) Rokland PID 920452 Inline JST-PH Power Switch Pocket + 10mm Deep LiPo Bay
// ============================================================================

/* [View & Export Selection] */
// Select which part or assembly to preview/export:
part_select = "Assembly_RAK"; // ["Assembly_RAK", "Assembly_WioL1", "CaseS1_DualRF", "CaseS1_DualRF_BoltOn", "CaseL1_Deep", "CaseL1_Deep_WioL1", "CaseM1_RAK", "CaseU1_RAK", "CaseM1_WioL1", "CaseU1_WioL1", "CaseButton_WioL1", "CaseJoystick", "CaseButton", "CaseR1", "CaseSlide"]
exploded_distance = 12.0; // [0:1:40]

/* [Fine-Tune Bulkhead & Switch Clearances (mm)] */
n_type_extra_clearance = 0.0; // [-0.3:0.05:0.5]
sma_extra_clearance = 0.0;    // [-0.3:0.05:0.5]

module part_s1() {{
    difference() {{
        import("../STL/Wio_Tracker_L1_{v}/CaseS1_DualRF_{v}.stl", convexity=10);
        if (n_type_extra_clearance > 0) {{
            translate([68.5, 9.0, -7.0])
                cylinder(d=6.5 + n_type_extra_clearance, h=6.0, $fn=64);
        }}
        if (sma_extra_clearance > 0) {{
            translate([48.5, 9.0, -7.0])
                cylinder(d=6.5 + sma_extra_clearance, h=6.0, $fn=64);
        }}
    }}
}}

module render_selected() {{
    if (part_select == "CaseS1_DualRF") {{
        part_s1();
    }} else if (part_select == "CaseS1_DualRF_BoltOn") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseS1_DualRF_BoltOn_{v}.stl", convexity=10);
    }} else if (part_select == "CaseL1_Deep") {{
        import("../STL/RAK_WisBlock_{v}/CaseL1_Deep_{v}.stl", convexity=10);
    }} else if (part_select == "CaseL1_Deep_WioL1") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseL1_Deep_WioL1_{v}.stl", convexity=10);
    }} else if (part_select == "CaseM1_RAK") {{
        import("../STL/RAK_WisBlock_{v}/CaseM1_RAK_{v}.stl", convexity=10);
    }} else if (part_select == "CaseU1_RAK") {{
        import("../STL/RAK_WisBlock_{v}/CaseU1_RAK_{v}.stl", convexity=10);
    }} else if (part_select == "CaseM1_WioL1") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseM1_WioL1_{v}.stl", convexity=10);
    }} else if (part_select == "CaseU1_WioL1") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseU1_WioL1_{v}.stl", convexity=10);
    }} else if (part_select == "CaseButton_WioL1") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseButton_WioL1_{v}.stl", convexity=10);
    }} else if (part_select == "CaseJoystick") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseJoystick_{v}.stl", convexity=10);
    }} else if (part_select == "CaseButton") {{
        import("../STL/RAK_WisBlock_{v}/CaseButton_{v}.stl", convexity=10);
    }} else if (part_select == "CaseR1") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseR1_{v}.stl", convexity=10);
    }} else if (part_select == "CaseSlide") {{
        import("../STL/Wio_Tracker_L1_{v}/CaseSlide_{v}.stl", convexity=10);
    }} else if (part_select == "Assembly_RAK") {{
        rotate([180, 0, 0]) {{
            color("#2b2d30") translate([0, 0, -exploded_distance]) part_s1();
            color("#f3f4f6") translate([0, 6.0, 0]) import("../STL/RAK_WisBlock_{v}/CaseM1_RAK_{v}.stl", convexity=10);
            color("#ea580c") translate([0, -exploded_distance, 2.0]) import("../STL/RAK_WisBlock_{v}/CaseL1_Deep_{v}.stl", convexity=10);
            color("#f97316") translate([0, 11.2 + exploded_distance, 2.0]) import("../STL/RAK_WisBlock_{v}/CaseU1_RAK_{v}.stl", convexity=10);
            color("#2b2d30") translate([6.5 - 3.5, 14.2 + exploded_distance * 1.35, 12.5 + 2.5]) rotate([0, 90, 0]) import("../STL/RAK_WisBlock_{v}/CaseButton_{v}.stl", convexity=10);
            color("#2b2d30") translate([0, 0, 41.0 + exploded_distance * 0.6]) import("../STL/RAK_WisBlock_{v}/CaseR1_{v}.stl", convexity=10);
            color("#1f2937") translate([5.25, 4.0, 43.0 + exploded_distance * 1.2]) import("../STL/RAK_WisBlock_{v}/CaseSlide_{v}.stl", convexity=10);
        }}
    }} else if (part_select == "Assembly_WioL1") {{
        rotate([180, 0, 0]) {{
            color("#2b2d30") translate([0, 0, -exploded_distance]) part_s1();
            color("#f3f4f6") translate([0, 6.0, 0]) import("../STL/Wio_Tracker_L1_{v}/CaseM1_WioL1_{v}.stl", convexity=10);
            color("#ea580c") translate([0, -exploded_distance, 2.0]) import("../STL/Wio_Tracker_L1_{v}/CaseL1_Deep_WioL1_{v}.stl", convexity=10);
            color("#f97316") translate([0, 11.2 + exploded_distance, 2.0]) import("../STL/Wio_Tracker_L1_{v}/CaseU1_WioL1_{v}.stl", convexity=10);
            color("#2b2d30") translate([31.45, 14.5 + exploded_distance * 1.35, 49.77]) rotate([-90, 0, 0]) import("../STL/Wio_Tracker_L1_{v}/CaseButton_WioL1_{v}.stl", convexity=10);
            color("#2b2d30") translate([44.24 - 4.8, 13.6 + exploded_distance * 1.35, 41.27 + 4.8]) rotate([-90, 0, 0]) import("../STL/Wio_Tracker_L1_{v}/CaseJoystick_{v}.stl", convexity=10);
            color("#2b2d30") translate([0, 0, 69.0 + exploded_distance * 0.6]) import("../STL/Wio_Tracker_L1_{v}/CaseR1_{v}.stl", convexity=10);
            color("#1f2937") translate([5.25, 4.0, 71.0 + exploded_distance * 1.2]) import("../STL/Wio_Tracker_L1_{v}/CaseSlide_{v}.stl", convexity=10);
        }}
    }}
}}

render_selected();
""".format(v=MODEL_VERSION)
    with open(scad_path, "w", encoding="utf-8") as f:
        f.write(scad_code)


def render_engineering_views(parts: dict[str, trimesh.Trimesh]) -> None:
    """Generate orthographic wireframe & cross-section engineering plots in renders/."""
    os.makedirs(OUT_RENDER_DIR, exist_ok=True)

    # 1. Individual Part Orthographic Blueprints
    key_parts = [
        ("CaseS1_DualRF_v2.0 (Dual-SMA)", parts["CaseS1_DualRF"], "#1f2937"),
        ("CaseS1_DualRF_BoltOn_v2.0 (4-Bolt N + M3 Nuts)", parts["CaseS1_DualRF_BoltOn"], "#0f172a"),
        ("CaseL1_Deep_v2.0", parts["CaseL1_Deep"], "#d97706"),
        ("CaseM1_RAK_v2.0", parts["CaseM1_RAK"], "#2563eb"),
        ("CaseU1_RAK_v2.0", parts["CaseU1_RAK"], "#dc2626"),
        ("CaseM1_WioL1_v2.0", parts["CaseM1_WioL1"], "#059669"),
        ("CaseU1_WioL1_v2.0", parts["CaseU1_WioL1"], "#7c3aed"),
    ]
    fig, axes = plt.subplots(len(key_parts), 3, figsize=(18, 3.6 * len(key_parts)))
    for row, (name, m, col) in enumerate(key_parts):
        v = m.vertices
        f = m.faces
        views = [
            (0, 2, -1, "Front / Back (X vs -Z)"),
            (0, 1, 1, "Top / Bottom (X vs Y)"),
            (1, 2, -1, "Side Profile (Y vs -Z)"),
        ]
        for c_idx, (ax_x, ax_y, sign_y, title) in enumerate(views):
            ax = axes[row, c_idx]
            ax.triplot(v[:, ax_x], sign_y * v[:, ax_y], f, lw=0.22, color=col)
            ax.set_aspect("equal")
            ax.set_title(f"{name} — {title}", fontsize=10, fontweight="bold")
            ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_RENDER_DIR, "MeshSlide_DualRF_Blueprints.png"), dpi=160)
    plt.close(fig)

    # 2. Assembled Cross-Section Comparison (RAK19007 Assembly vs Wio Tracker L1 Assembly)
    fig, axes = plt.subplots(2, 2, figsize=(18, 13))
    for row, (label, s1_key, m1_key, u1_key, l1_key, r1_z, slide_z) in enumerate([
        ("Pairing A (v2.0): RAK19007 + Dual-SMA Top Rail (45mm Body)", "CaseS1_DualRF", "CaseM1_RAK", "CaseU1_RAK", "CaseL1_Deep", 41.0, 43.0),
        ("Pairing B (v2.0): Seeed Wio Tracker L1 + 4-Bolt N-Type Top Rail (73mm Body)", "CaseS1_DualRF_BoltOn", "CaseM1_WioL1", "CaseU1_WioL1", "CaseL1_Deep_WioL1", 69.0, 71.0),
    ]):
        assy_parts = [
            (s1_key, parts[s1_key].copy(), "#111827"),
            (m1_key, parts[m1_key].copy().apply_translation([0, 6.0, 0.0]), "#2563eb"),
            (l1_key, parts[l1_key].copy().apply_translation([0, 0.0, 2.0]), "#ea580c"),
            (u1_key, parts[u1_key].copy().apply_translation([0, 11.2, 2.0]), "#dc2626"),
            ("CaseR1", parts["CaseR1"].copy().apply_translation([0, 0.0, r1_z]), "#374151"),
            ("CaseSlide", parts["CaseSlide"].copy().apply_translation([5.25, 4.0, slide_z]), "#0284c7"),
        ]
        # Y-Z Cross Section at X=35mm (through OLED & Battery bay)
        ax_yz = axes[row, 0]
        for pname, pm, pcol in assy_parts:
            sec = pm.section(plane_origin=[35.0, 0, 0], plane_normal=[1, 0, 0])
            if sec:
                for ent in sec.entities:
                    pts = sec.vertices[ent.points]
                    ax_yz.plot(pts[:, 1], -pts[:, 2], color=pcol, lw=1.6)
        ax_yz.set_aspect("equal")
        ax_yz.set_title(f"{label}\nY-Z Section at X=35mm (10mm Deep Battery + OLED + Slide Rail)", fontsize=10, fontweight="bold")
        ax_yz.set_xlabel("Y (mm) [-4=Back Cover, 18=Front Face]")
        ax_yz.set_ylabel("-Z (mm) [+7.2=Top Rail, -79.1=Bottom Pogo Rail]")
        ax_yz.grid(True, alpha=0.35)

        # X-Z Cross Section at Y=9mm (through N-Type/SMA, Board Tray, and Pogo Rail)
        ax_xz = axes[row, 1]
        for pname, pm, pcol in assy_parts:
            sec = pm.section(plane_origin=[0, 9.0, 0], plane_normal=[0, 1, 0])
            if sec:
                for ent in sec.entities:
                    pts = sec.vertices[ent.points]
                    ax_xz.plot(pts[:, 0], -pts[:, 2], color=pcol, lw=1.6, label=pname)
        ax_xz.set_aspect("equal")
        ax_xz.set_title(f"{label}\nX-Z Section at Y=9mm (GPS SMA @ X=48.5, 915MHz @ X=68.5, Pogo Rail)", fontsize=10, fontweight="bold")
        ax_xz.set_xlabel("X (mm) [0=Left USB-C & Switch, 96.5=Right Side]")
        ax_xz.set_ylabel("-Z (mm)")
        ax_xz.grid(True, alpha=0.35)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_RENDER_DIR, "MeshSlide_DualRF_Assembled_Sections.png"), dpi=160)
    plt.close(fig)

    # 2b. CardKB Pro Hybrid Orthographic Blueprints & Cross-Sections
    kb_parts_plot = [
        ("KB_S1_Pro (MeshSlide Top Bezel)", parts["KB_S1_Pro"], "#2563eb"),
        ("KB_S3_Pro (Ultra-Slim SlideKB Back)", parts["KB_S3_Pro"], "#059669"),
        ("CardKB_Standalone_Bezel", parts["CardKB_Standalone_Bezel"], "#7c3aed"),
        ("CardKB_Standalone_Back", parts["CardKB_Standalone_Back"], "#4b5563"),
        ("KB_Buttons_Bridged_Tray (PETG/PLA)", parts["KB_Buttons_Bridged_Tray"], "#0284c7"),
        ("KB_TPU_Mat (Flexible TPU 95A)", parts["KB_TPU_Mat"], "#dc2626"),
    ]
    fig_kb, axes_kb = plt.subplots(len(kb_parts_plot), 2, figsize=(16, 3.2 * len(kb_parts_plot)))
    for row, (name, m, col) in enumerate(kb_parts_plot):
        v = m.vertices
        f = m.faces
        ax0 = axes_kb[row, 0]
        if name.startswith("KB_S"):
            ax0.triplot(-v[:, 2], -v[:, 0], f, lw=0.20, color=col)
            ax0.set_title(f"{name} — Front/Back View (-Z vs -X)", fontsize=9.5, fontweight="bold")
        else:
            ax0.triplot(v[:, 0], v[:, 1], f, lw=0.20, color=col)
            ax0.set_title(f"{name} — Top/Bottom View (X vs Y)", fontsize=9.5, fontweight="bold")
        ax0.set_aspect("equal")
        ax0.grid(True, alpha=0.3)

        ax1 = axes_kb[row, 1]
        if name.startswith("KB_S"):
            ax1.triplot(v[:, 0], v[:, 1], f, lw=0.20, color=col)
            ax1.set_title(f"{name} — Side Profile (X vs Y)", fontsize=9.5, fontweight="bold")
        else:
            ax1.triplot(v[:, 0], v[:, 2], f, lw=0.20, color=col)
            ax1.set_title(f"{name} — Side Profile (X vs Z)", fontsize=9.5, fontweight="bold")
        ax1.set_aspect("equal")
        ax1.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_RENDER_DIR, "CardKB_Pro_Blueprints.png"), dpi=160)
    plt.close(fig_kb)

    # 2c. CardKB Pro Assembled Cross-Section Stackup (SlideKB_Pro & Standalone_Pro)
    fig_sec, axes_sec = plt.subplots(2, 1, figsize=(16, 9))
    T_s3 = np.array([
        [1.0,  0.0,  0.0, -3.80],
        [0.0, -1.0,  0.0,  0.00],
        [0.0,  0.0, -1.0, 96.50],
        [0.0,  0.0,  0.0,  1.00],
    ])
    slidekb_assy = [
        ("KB_S1_Pro (Bezel)", parts["KB_S1_Pro"].copy(), "#1f2937"),
        ("KB_Buttons_Bridged (PETG/PLA)", pcb_to_s1_transform(parts["KB_Buttons_Bridged_Tray"]), "#2563eb"),
        ("KB_TPU_Mat (TPU 95A)", pcb_to_s1_transform(parts["KB_TPU_Mat"]), "#dc2626"),
        ("KB_S3_Pro (Slim Back)", parts["KB_S3_Pro"].copy().apply_transform(T_s3), "#059669"),
    ]
    ax_s0 = axes_sec[0]
    for pname, pm, pcol in slidekb_assy:
        sec = pm.section(plane_origin=[34.20, 0, 0], plane_normal=[1, 0, 0])
        if sec:
            for ent in sec.entities:
                pts = sec.vertices[ent.points]
                ax_s0.plot(-pts[:, 2], pts[:, 1], color=pcol, lw=1.4, label=pname)
                pname = "_nolegend_"
    ax_s0.set_aspect("equal")
    ax_s0.set_title("SlideKB_Pro Assembled Z-Y Cross-Section through Row 1 (X_S1 = 34.20 mm) — Back-Loaded Keys + TPU Plunger Mat + Slim Back", fontsize=10.5, fontweight="bold")
    ax_s0.set_xlabel("-Z_S1 (mm) [Left to Right]")
    ax_s0.set_ylabel("Y_S1 (mm) [-2.6=Slim Back, 7.0=Bezel Face, 7.55=Button Top]")
    ax_s0.legend(loc="upper right", fontsize=8.5)
    ax_s0.grid(True, alpha=0.35)

    standalone_assy = [
        ("CardKB_Standalone_Bezel", parts["CardKB_Standalone_Bezel"].copy().apply_translation([-4.0, -3.0, 0.0]), "#7c3aed"),
        ("KB_Buttons_Bridged (PETG/PLA)", parts["KB_Buttons_Bridged_Tray"].copy(), "#2563eb"),
        ("KB_TPU_Mat (TPU 95A)", parts["KB_TPU_Mat"].copy(), "#dc2626"),
        ("CardKB_Standalone_Back", parts["CardKB_Standalone_Back"].copy().apply_translation([-4.0, -3.0, -2.80]), "#374151"),
    ]
    ax_s1 = axes_sec[1]
    for pname, pm, pcol in standalone_assy:
        sec = pm.section(plane_origin=[0, 30.70, 0], plane_normal=[0, 1, 0])
        if sec:
            for ent in sec.entities:
                pts = sec.vertices[ent.points]
                ax_s1.plot(pts[:, 0], pts[:, 2], color=pcol, lw=1.4, label=pname)
                pname = "_nolegend_"
    ax_s1.set_aspect("equal")
    ax_s1.set_title("CardKB_Standalone_Pro Assembled X-Z Cross-Section through Row 1 (Y_pcb = 30.70 mm) — 100% Shared Button & TPU Stackup", fontsize=10.5, fontweight="bold")
    ax_s1.set_xlabel("X_pcb (mm) [-4.0=Left Border, 88.0=Right Border]")
    ax_s1.set_ylabel("Z_pcb (mm) [-2.8=Backplate Bottom, 0.0=PCB Top, 6.4=Bezel Top, 6.95=Button Top]")
    ax_s1.legend(loc="upper right", fontsize=8.5)
    ax_s1.grid(True, alpha=0.35)

    plt.tight_layout()
    plt.savefig(os.path.join(OUT_RENDER_DIR, "CardKB_Pro_Assembled_Sections.png"), dpi=160)
    plt.close(fig_sec)

    # 3. 3D Shaded Assembly & Exploded Renders via OpenSCAD CLI (if installed)
    scad_cli = r"C:\Program Files\OpenSCAD\openscad.com"
    scad_file = os.path.join(OUT_SCAD_DIR, "MeshSlide_DualRF.scad")
    if os.path.isfile(scad_cli) and os.path.isfile(scad_file):
        for out_name, part_sel, exp_dist, cam in [
            ("Assembly_WioL1_3D.png", "Assembly_WioL1", 0, "48,-9,-31,68,0,322,265"),
            ("Assembly_WioL1_Exploded_3D.png", "Assembly_WioL1", 12, "48,-9,-31,68,0,322,315"),
            ("Assembly_RAK_3D.png", "Assembly_RAK", 0, "48,-9,-22,68,0,322,235"),
            ("Assembly_RAK_Exploded_3D.png", "Assembly_RAK", 12, "48,-9,-22,68,0,322,285"),
            ("Assembly_Rear_Left_3D.png", "Assembly_WioL1", 0, "45,-9,-31,68,0,225,265"),
        ]:
            subprocess.run(
                [
                    scad_cli,
                    "-o",
                    os.path.join(OUT_RENDER_DIR, out_name),
                    "-D",
                    f'part_select="{part_sel}"',
                    "-D",
                    f"exploded_distance={exp_dist}",
                    "--imgsize=1200,850",
                    "--colorscheme=Tomorrow Night",
                    f"--camera={cam}",
                    scad_file,
                ],
                check=True,
            )


def main() -> None:
    os.makedirs(OUT_STL_DIR, exist_ok=True)
    os.makedirs(OUT_STEP_DIR, exist_ok=True)
    os.makedirs(OUT_3MF_DIR, exist_ok=True)

    print("Building MeshSlide-DualRF CAD parts...")
    parts = {
        "CaseS1_DualRF": build_case_s1_dual_rf(),
        "CaseS1_DualRF_BoltOn": build_case_s1_dual_rf_bolton(),
        "CaseS1_DualRF_Heatset": build_case_s1_dual_rf_heatset(),
        "CaseL1_Deep": build_case_l1_deep(with_rokland_switch=True),
        "CaseL1_Deep_WioL1": build_case_l1_deep(with_rokland_switch=False),
        "CaseR1": build_case_r1(),
        "CaseSlide": build_case_slide(),
        "CaseButton": build_case_button(),
        "CaseButton_WioL1": build_case_button_wio_l1(),
        "CaseJoystick": build_case_joystick_wio_l1(),
        "CaseM1_RAK": build_case_m1_rak(),
        "CaseU1_RAK": build_case_u1_rak(),
        "CaseM1_WioL1": build_case_m1_wio_l1(),
        "CaseU1_WioL1": build_case_u1_wio_l1(),
        "KB_TPU_Mat": build_kb_tpu_mat(),
        "KB_Button_Single_Main": build_kb_button_single(),
        "KB_Buttons_Loose_Set": build_kb_buttons_loose_set(),
        "KB_Buttons_Bridged_Tray": build_kb_buttons_bridged(),
        "KB_Bezel_Legends_AMS": build_kb_bezel_legends_ams(),
        "KB_S1_Pro": build_kb_s1_pro(),
        "KB_S3_Pro": build_kb_s3_pro(),
        "CardKB_Standalone_Bezel": build_cardkb_standalone_bezel(),
        "CardKB_Standalone_Back": build_cardkb_standalone_back(),
    }

    for name, mesh in parts.items():
        b = mesh.bounds
        dims = b[1] - b[0]
        print(
            f"  [OK] {name:24s} | watertight={str(mesh.is_watertight):5s} | "
            f"dims=({dims[0]:5.2f} x {dims[1]:5.2f} x {dims[2]:5.2f} mm) | vol={mesh.volume:8.1f} mm^3"
        )

    # Populate clean, self-contained folders for Wio_Tracker_L1, RAK_WisBlock, and CardKB_Pro
    wio_parts = [
        "CaseS1_DualRF",
        "CaseS1_DualRF_BoltOn",
        "CaseS1_DualRF_Heatset",
        "CaseL1_Deep_WioL1",
        "CaseM1_WioL1",
        "CaseU1_WioL1",
        "CaseButton_WioL1",
        "CaseJoystick",
        "CaseR1",
        "CaseSlide",
    ]
    rak_parts = [
        "CaseS1_DualRF",
        "CaseS1_DualRF_BoltOn",
        "CaseS1_DualRF_Heatset",
        "CaseL1_Deep",
        "CaseM1_RAK",
        "CaseU1_RAK",
        "CaseButton",
        "CaseR1",
        "CaseSlide",
    ]
    cardkb_pro_parts = [
        "KB_TPU_Mat",
        "KB_Button_Single_Main",
        "KB_Buttons_Loose_Set",
        "KB_Buttons_Bridged_Tray",
        "KB_Bezel_Legends_AMS",
        "KB_S1_Pro",
        "KB_S3_Pro",
        "CardKB_Standalone_Bezel",
        "CardKB_Standalone_Back",
    ]

    wio_dir = f"Wio_Tracker_L1_{MODEL_VERSION}"
    rak_dir = f"RAK_WisBlock_{MODEL_VERSION}"
    kb_dir = f"CardKB_Pro_{MODEL_VERSION}"

    for ext, base_dir in [("stl", OUT_STL_DIR), ("step", OUT_STEP_DIR)]:
        os.makedirs(os.path.join(base_dir, wio_dir), exist_ok=True)
        os.makedirs(os.path.join(base_dir, rak_dir), exist_ok=True)
        os.makedirs(os.path.join(base_dir, kb_dir), exist_ok=True)

        for p in wio_parts:
            vname = f"{p}_{MODEL_VERSION}"
            out_p = os.path.join(base_dir, wio_dir, f"{vname}.{ext}")
            parts[p].export(out_p) if ext == "stl" else export_step_ap214(parts[p], out_p, part_name=vname)

        for p in rak_parts:
            vname = f"{p}_{MODEL_VERSION}"
            out_p = os.path.join(base_dir, rak_dir, f"{vname}.{ext}")
            parts[p].export(out_p) if ext == "stl" else export_step_ap214(parts[p], out_p, part_name=vname)

        for p in cardkb_pro_parts:
            vname = f"{p}_{MODEL_VERSION}"
            out_p = os.path.join(base_dir, kb_dir, f"{vname}.{ext}")
            parts[p].export(out_p) if ext == "stl" else export_step_ap214(parts[p], out_p, part_name=vname)

    print(f"Exporting single unified 3MF print plate ({MODEL_VERSION})...")
    single_3mf_path = os.path.join(OUT_3MF_DIR, f"Wio_Tracker_L1_Complete_{MODEL_VERSION}.3mf")
    export_3mf_bundle(
        {f"{k}_{MODEL_VERSION}": parts[k] for k in wio_parts},
        single_3mf_path,
    )
    import shutil
    shutil.copy2(single_3mf_path, os.path.join(os.path.dirname(OUT_3MF_DIR), f"Wio_Tracker_L1_Complete_{MODEL_VERSION}.3mf"))

    print("Generating OpenSCAD Customizer project...")
    generate_openscad_customizer()

    print("Rendering orthographic engineering blueprints & cross sections...")
    render_engineering_views(parts)
    print("Done!")


if __name__ == "__main__":
    main()
