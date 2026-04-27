"""
Project 4 — Kitchen Elevations + 3D Cabinetry.

Single-wall kitchen: 14'-0" wide × 10'-0" deep × 10'-0" ceiling.
- Long-wall cabinet run (south wall) totaling 168":
    B36 + R30 + DW24 + SB36 + B30 + P12 (substitutes DW24 for one of brief's
    base cabinets so the run fits the 14' wall — documented in SPEC §8)
- Wall cabinets above, 42" tall starting at 54" AFF
- Range hood instead of a wall cab over the range
- Pantry tall cabinet 84" full-height
- Island 96" × 42" with 12" overhang on the north (seating) side, toe kick
  on south (storage) side
- Counter 1.5" thick, 25.5" deep on the wall run, with sink subtract
- Appliances as boxes on I-FURN-APPL: range, range hood, dishwasher
"""
from __future__ import annotations

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


# Room geometry
W = 168.0   # 14' wide  (X)
D = 120.0   # 10' deep (Y)
H = 120.0   # 10' ceiling (Z)
WALL = 4.0
SLAB = 2.0
CEILING_TH = 4.0

# Cabinet run heights
BASE_H = 34.5
COUNTER_TH = 1.5
COUNTER_H = BASE_H + COUNTER_TH                  # 36
WALL_CAB_BOTTOM = 54.0
WALL_CAB_H = 42.0
WALL_CAB_TOP = WALL_CAB_BOTTOM + WALL_CAB_H      # 96
HOOD_BOTTOM = 66.0
HOOD_H = 30.0
PANTRY_H = 84.0

BASE_DEPTH = 24.0     # cabinet body depth
COUNTER_DEPTH = 25.5  # 1.5" overhang on front
WALL_CAB_DEPTH = 12.0
HOOD_DEPTH = 18.0
TOE_TALL = 4.0
TOE_DEEP = 3.0

# Cabinet x-positions along south wall (y=0 is wall face)
RUN = [
    ("B36",  0,    36),
    ("R30",  36,   66),    # range slot — no cabinet body, just appliance
    ("DW24", 66,   90),    # dishwasher slot
    ("SB36", 90,   126),
    ("B30",  126,  156),
    ("P12",  156,  168),   # tall pantry
]

# Island geometry
ISL_X1, ISL_X2 = 36.0, 132.0     # 96" wide
ISL_Y1, ISL_Y2 = 51.0, 93.0      # 42" deep, centered (60-21..60+21)... actually 51-93 for 60+12 area
ISL_OVERHANG = 12.0              # on seating side (north / +Y)
ISL_COUNTER_X1 = ISL_X1 - 1.5
ISL_COUNTER_X2 = ISL_X2 + 1.5
ISL_COUNTER_Y1 = ISL_Y1
ISL_COUNTER_Y2 = ISL_Y2 + ISL_OVERHANG

# ACI palette
ACI_WOOD_FLOOR = 40       # warm walnut for floor
ACI_WHITE = 254           # walls/ceiling
ACI_CABINET_PAINT = 33    # cream painted cabinet
ACI_COUNTER_QUARTZ = 8    # quartz light gray
ACI_HOOD_STAINLESS = 9    # stainless
ACI_RANGE_BLACK = 252     # black appliance
ACI_DW_STAINLESS = 9
ACI_SINK_STAINLESS = 8
ACI_PANTRY_PAINT = 33
ACI_TRIM_WHITE = 254
ACI_FAUCET = 9


def clear_modelspace(a: Acad) -> int:
    n = 0
    while a.doc.ModelSpace.Count > 0:
        try:
            a.doc.ModelSpace.Item(0).Delete()
            n += 1
        except Exception:
            break
    return n


def main():
    a = Acad()
    print("[1] cancel + connect")
    a.cancel(); time.sleep(0.5); a.connect(); a.wait_idle(5)
    print(f"    doc={a.doc.Name} entities={a.doc.ModelSpace.Count}")

    if "kitchen" not in a.doc.Name.lower():
        raise SystemExit("active doc is not kitchen.dwg")

    # Suppress dialogs (carry-forward learning from session 4-27)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)
    sv("LUNITS", 4); sv("INSUNITS", 1)
    sv("DEFAULTLIGHTING", 0)
    sv("LIGHTINGUNITS", 2)

    print("[2] purge model space")
    print(f"    removed {clear_modelspace(a)}")

    print("[3] layers")
    layers = [
        ("A-WALL",         ACI_WHITE),
        ("A-FLOR",         ACI_WOOD_FLOOR),
        ("A-CLNG",         ACI_WHITE),
        ("A-TRIM",         ACI_TRIM_WHITE),
        ("I-CASE",         ACI_CABINET_PAINT),     # cabinets
        ("I-CASE-ISLA",    ACI_CABINET_PAINT),     # island casework
        ("I-CASE-CTR",     ACI_COUNTER_QUARTZ),    # countertop
        ("I-CASE-WALL",    ACI_CABINET_PAINT),     # wall cabinets
        ("I-CASE-PANT",    ACI_PANTRY_PAINT),      # pantry
        ("I-FURN-APPL",    ACI_RANGE_BLACK),       # appliances
        ("I-FURN-APPL-MTL", ACI_HOOD_STAINLESS),    # stainless metal
        ("I-FURN-SINK",    ACI_SINK_STAINLESS),    # sink basin
    ]
    for name, ci in layers:
        a.create_layer(name, ci)

    # ------------------------------------------------------------------
    # SHELL — floor, walls, ceiling
    # ------------------------------------------------------------------
    print("[4] shell")
    a.set_active_layer("A-FLOR")
    a.add_box([0, 0, -SLAB], [W, D, 0])

    a.set_active_layer("A-WALL")
    south = a.add_box([-WALL, -WALL, 0], [W + WALL, 0,        H])
    north = a.add_box([-WALL,  D,    0], [W + WALL, D + WALL, H])
    east  = a.add_box([ W,     0,    0], [W + WALL, D,        H])
    west  = a.add_box([-WALL,  0,    0], [0,        D,        H])

    # Hallway opening on west wall (kitchen connects to dining/living)
    print("    hallway opening on west wall")
    hall_void = a.add_box([-WALL - 1, 24, 0], [1, 96, 96])
    a.boolean("subtract", [west["handle"]], [hall_void["handle"]])

    # Ceiling slab
    a.set_active_layer("A-CLNG")
    a.add_box([0, 0, H], [W, D, H + CEILING_TH])

    # ------------------------------------------------------------------
    # WALL-RUN CABINETS (south wall, y=0..24 base, y=0..12 wall cab)
    # ------------------------------------------------------------------
    print("[5] long-wall cabinet run")

    # Base cabinet bodies (skip range, dishwasher, pantry slots — those are
    # appliances or pantry handled separately)
    a.set_active_layer("I-CASE")
    base_cab_slots = [s for s in RUN if s[0].startswith("B") or s[0].startswith("SB")]
    for tag, x1, x2 in base_cab_slots:
        # Body: 24" deep, 34.5" tall; toe kick is recessed 3" at bottom 4"
        # Make full-depth box then SUBTRACT toe kick void (PRESSPULL substitute)
        body = a.add_box([x1, 0, 0], [x2, BASE_DEPTH, BASE_H])
        toe_void = a.add_box([x1 - 0.1, 0, 0], [x2 + 0.1, TOE_DEEP, TOE_TALL])
        a.boolean("subtract", [body["handle"]], [toe_void["handle"]])
        print(f"    {tag}: x={x1}..{x2} (with toe kick)")

    # Pantry — full-height tall cabinet
    print("    pantry P12")
    a.set_active_layer("I-CASE-PANT")
    pantry = a.add_box([156, 0, 0], [168, BASE_DEPTH, PANTRY_H])
    pantry_toe = a.add_box([156 - 0.1, 0, 0], [168 + 0.1, TOE_DEEP, TOE_TALL])
    a.boolean("subtract", [pantry["handle"]], [pantry_toe["handle"]])

    # Counter top — single span, with sink cutout
    print("    counter (single span with sink subtract)")
    a.set_active_layer("I-CASE-CTR")
    # Range gap: counter splits at the range body; brief shows continuous
    # counter, so we'll have continuous counter except an opening over the
    # sink. Range has its own cooking surface so counter ends at range edges.
    counter_left = a.add_box([0, 0, BASE_H], [36, COUNTER_DEPTH, COUNTER_H])
    counter_right = a.add_box([66, 0, BASE_H], [156, COUNTER_DEPTH, COUNTER_H])
    # (skip pantry — pantry is full-height, counter ends at x=156)
    # Sink subtract from counter_right
    sink_void = a.add_box([100, 3, BASE_H - 0.1], [126, 22, COUNTER_H + 0.1])
    a.boolean("subtract", [counter_right["handle"]], [sink_void["handle"]])

    # Sink basin (visible inside the cutout)
    print("    sink basin")
    a.set_active_layer("I-FURN-SINK")
    a.add_box([101, 4, BASE_H - 9], [125, 21, BASE_H - 0.5])

    # Wall cabinets — 42" tall, 12" deep, start at z=54
    print("    wall cabinets")
    a.set_active_layer("I-CASE-WALL")
    wall_cab_slots = [
        ("WC36", 0,   36),     # over B36
        # over R30 -> hood instead, no wall cab
        ("WC24", 66,  90),     # over DW
        ("WC36", 90,  126),    # over SB36
        ("WC30", 126, 156),    # over B30
        # pantry takes wall cab area at x=156..168 (already tall full-height)
    ]
    for tag, x1, x2 in wall_cab_slots:
        a.add_box([x1, 0, WALL_CAB_BOTTOM], [x2, WALL_CAB_DEPTH, WALL_CAB_TOP])
        print(f"    {tag}: x={x1}..{x2}")

    # Range hood
    print("    range hood")
    a.set_active_layer("I-FURN-APPL-MTL")
    a.add_box([36, 0, HOOD_BOTTOM], [66, HOOD_DEPTH, HOOD_BOTTOM + HOOD_H])
    # vent hood "neck" up to ceiling
    a.add_box([46, 0, HOOD_BOTTOM + HOOD_H], [56, 6, H])

    # Range body
    print("    range")
    a.set_active_layer("I-FURN-APPL")
    a.add_box([36, 0, 0], [66, 27, 36])
    # cooktop grates as 4 small cylinders
    a.set_active_layer("I-FURN-APPL-MTL")
    for cx in [44, 58]:
        for cy in [10, 22]:
            a.add_cylinder([cx, cy, 36], 2.5, 0.3)

    # Dishwasher
    print("    dishwasher")
    a.set_active_layer("I-FURN-APPL-MTL")
    a.add_box([66, 0, 0], [90, 24, BASE_H])

    # ------------------------------------------------------------------
    # ISLAND
    # ------------------------------------------------------------------
    print("[6] island")
    a.set_active_layer("I-CASE-ISLA")
    isl_body = a.add_box([ISL_X1, ISL_Y1, 0], [ISL_X2, ISL_Y2, BASE_H])
    # Toe kick on south (storage) side: notch at y=ISL_Y1
    isl_toe = a.add_box([ISL_X1 - 0.1, ISL_Y1, 0],
                        [ISL_X2 + 0.1, ISL_Y1 + TOE_DEEP, TOE_TALL])
    a.boolean("subtract", [isl_body["handle"]], [isl_toe["handle"]])

    # Island counter — overhangs north (seating) by 12", sides by 1.5"
    a.set_active_layer("I-CASE-CTR")
    a.add_box([ISL_COUNTER_X1, ISL_COUNTER_Y1, BASE_H],
              [ISL_COUNTER_X2, ISL_COUNTER_Y2, COUNTER_H])

    # ------------------------------------------------------------------
    # FAUCET — small cylinder behind sink
    # ------------------------------------------------------------------
    print("[7] faucet")
    a.set_active_layer("I-FURN-APPL-MTL")
    a.add_cylinder([113, 23, COUNTER_H], 0.6, 12.0)
    # spout: another short cylinder offset
    a.add_cylinder([113, 23, COUNTER_H + 12], 0.5, 1.0)

    # ------------------------------------------------------------------
    # FREEZE CEILING + SET VIEW
    # ------------------------------------------------------------------
    print("[8] freeze ceiling, set SW iso, save")
    try:
        a.freeze_layer("A-CLNG", freeze=True)
    except Exception:
        pass
    try:
        a.set_view("SWISO"); a.wait_idle(5)
        a.set_visual_style("Conceptual"); a.wait_idle(5)
    except Exception as e:
        print(f"    view/style: {e}")
    a.zoom_extents()
    a.save()
    print(f"DONE entities={a.doc.ModelSpace.Count}")


if __name__ == "__main__":
    main()
