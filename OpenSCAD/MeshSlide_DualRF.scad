// ============================================================================
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

module part_s1() {
    difference() {
        import("../STL/Wio_Tracker_L1_v2.0/CaseS1_DualRF_v2.0.stl", convexity=10);
        if (n_type_extra_clearance > 0) {
            translate([68.5, 9.0, -7.0])
                cylinder(d=6.5 + n_type_extra_clearance, h=6.0, $fn=64);
        }
        if (sma_extra_clearance > 0) {
            translate([48.5, 9.0, -7.0])
                cylinder(d=6.5 + sma_extra_clearance, h=6.0, $fn=64);
        }
    }
}

module render_selected() {
    if (part_select == "CaseS1_DualRF") {
        part_s1();
    } else if (part_select == "CaseS1_DualRF_BoltOn") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseS1_DualRF_BoltOn_v2.0.stl", convexity=10);
    } else if (part_select == "CaseL1_Deep") {
        import("../STL/RAK_WisBlock_v2.0/CaseL1_Deep_v2.0.stl", convexity=10);
    } else if (part_select == "CaseL1_Deep_WioL1") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseL1_Deep_WioL1_v2.0.stl", convexity=10);
    } else if (part_select == "CaseM1_RAK") {
        import("../STL/RAK_WisBlock_v2.0/CaseM1_RAK_v2.0.stl", convexity=10);
    } else if (part_select == "CaseU1_RAK") {
        import("../STL/RAK_WisBlock_v2.0/CaseU1_RAK_v2.0.stl", convexity=10);
    } else if (part_select == "CaseM1_WioL1") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseM1_WioL1_v2.0.stl", convexity=10);
    } else if (part_select == "CaseU1_WioL1") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseU1_WioL1_v2.0.stl", convexity=10);
    } else if (part_select == "CaseButton_WioL1") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseButton_WioL1_v2.0.stl", convexity=10);
    } else if (part_select == "CaseJoystick") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseJoystick_v2.0.stl", convexity=10);
    } else if (part_select == "CaseButton") {
        import("../STL/RAK_WisBlock_v2.0/CaseButton_v2.0.stl", convexity=10);
    } else if (part_select == "CaseR1") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseR1_v2.0.stl", convexity=10);
    } else if (part_select == "CaseSlide") {
        import("../STL/Wio_Tracker_L1_v2.0/CaseSlide_v2.0.stl", convexity=10);
    } else if (part_select == "Assembly_RAK") {
        rotate([180, 0, 0]) {
            color("#2b2d30") translate([0, 0, -exploded_distance]) part_s1();
            color("#f3f4f6") translate([0, 6.0, 0]) import("../STL/RAK_WisBlock_v2.0/CaseM1_RAK_v2.0.stl", convexity=10);
            color("#ea580c") translate([0, -exploded_distance, 2.0]) import("../STL/RAK_WisBlock_v2.0/CaseL1_Deep_v2.0.stl", convexity=10);
            color("#f97316") translate([0, 11.2 + exploded_distance, 2.0]) import("../STL/RAK_WisBlock_v2.0/CaseU1_RAK_v2.0.stl", convexity=10);
            color("#2b2d30") translate([6.5 - 3.5, 14.2 + exploded_distance * 1.35, 12.5 + 2.5]) rotate([0, 90, 0]) import("../STL/RAK_WisBlock_v2.0/CaseButton_v2.0.stl", convexity=10);
            color("#2b2d30") translate([0, 0, 41.0 + exploded_distance * 0.6]) import("../STL/RAK_WisBlock_v2.0/CaseR1_v2.0.stl", convexity=10);
            color("#1f2937") translate([5.25, 4.0, 43.0 + exploded_distance * 1.2]) import("../STL/RAK_WisBlock_v2.0/CaseSlide_v2.0.stl", convexity=10);
        }
    } else if (part_select == "Assembly_WioL1") {
        rotate([180, 0, 0]) {
            color("#2b2d30") translate([0, 0, -exploded_distance]) part_s1();
            color("#f3f4f6") translate([0, 6.0, 0]) import("../STL/Wio_Tracker_L1_v2.0/CaseM1_WioL1_v2.0.stl", convexity=10);
            color("#ea580c") translate([0, -exploded_distance, 2.0]) import("../STL/Wio_Tracker_L1_v2.0/CaseL1_Deep_WioL1_v2.0.stl", convexity=10);
            color("#f97316") translate([0, 11.2 + exploded_distance, 2.0]) import("../STL/Wio_Tracker_L1_v2.0/CaseU1_WioL1_v2.0.stl", convexity=10);
            color("#2b2d30") translate([31.45, 14.5 + exploded_distance * 1.35, 49.77]) rotate([-90, 0, 0]) import("../STL/Wio_Tracker_L1_v2.0/CaseButton_WioL1_v2.0.stl", convexity=10);
            color("#2b2d30") translate([44.24 - 4.8, 13.6 + exploded_distance * 1.35, 41.27 + 4.8]) rotate([-90, 0, 0]) import("../STL/Wio_Tracker_L1_v2.0/CaseJoystick_v2.0.stl", convexity=10);
            color("#2b2d30") translate([0, 0, 69.0 + exploded_distance * 0.6]) import("../STL/Wio_Tracker_L1_v2.0/CaseR1_v2.0.stl", convexity=10);
            color("#1f2937") translate([5.25, 4.0, 71.0 + exploded_distance * 1.2]) import("../STL/Wio_Tracker_L1_v2.0/CaseSlide_v2.0.stl", convexity=10);
        }
    }
}

render_selected();
