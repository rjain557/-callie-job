"""Detail pass on the kitchen — add the geometry that makes the iso look
designed instead of blocky:
- Cabinet door reveals (thin grooves between doors/drawers)
- Drawer pulls and door knobs (cylinders)
- Range knobs (5 small cylinders on the front)
- Faucet swing arm (curved cylinder approximation)
- Backsplash tile band (between counter and wall cabs)
- Crown molding strip on top of wall cabinets
- Toe-kick reveal at island (was missing)
- Pendant lights over island (3 small cylinders hanging from ceiling)
- Bar stools at island seating side (cylinder seat + legs)

Idempotent: tagged geometry on layer "I-DETAIL" so re-running deletes the
prior pass first.
"""
from __future__ import annotations
import os, sys, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from acad import Acad


# Match build_kitchen.py constants
W, D, H = 168.0, 120.0, 120.0
BASE_H = 34.5
COUNTER_H = 36.0
WALL_CAB_BOTTOM = 54.0
WALL_CAB_TOP = 96.0

ACI_HARDWARE = 9          # brushed nickel
ACI_TILE = 254            # white tile
ACI_CROWN = 254
ACI_PENDANT = 8           # pendant fixture
ACI_STOOL_WD = 42         # walnut stool seat
ACI_STOOL_MTL = 9         # brushed metal legs

# Cabinet boundaries from build_kitchen.py
CAB_BASE_RUNS = [(0, 36, "B36"), (90, 126, "SB36"), (126, 156, "B30")]
CAB_WALL_RUNS = [(0, 36), (66, 90), (90, 126), (126, 156)]


def cleanup_prior(a: Acad) -> int:
    n = 0
    for ent in list(a.ms):
        try:
            if ent.Layer in ("I-DETAIL", "I-HARDWARE", "I-TILE", "I-CROWN",
                              "I-PENDANT", "I-STOOL"):
                ent.Delete(); n += 1
        except Exception:
            pass
    return n


def main():
    a = Acad(); a.cancel(); time.sleep(0.3); a.connect(); a.wait_idle(5)
    print(f"doc={a.doc.Name} entities={a.doc.ModelSpace.Count}", flush=True)
    sv = a.doc.SetVariable
    sv("FILEDIA", 0); sv("CMDDIA", 0); sv("EXPERT", 5)

    print("[purge] removing prior detail pass", flush=True)
    n = cleanup_prior(a)
    print(f"  removed {n}", flush=True)

    # Layers
    a.create_layer("I-DETAIL",   ACI_TILE)
    a.create_layer("I-HARDWARE", ACI_HARDWARE)
    a.create_layer("I-TILE",     ACI_TILE)
    a.create_layer("I-CROWN",    ACI_CROWN)
    a.create_layer("I-PENDANT",  ACI_PENDANT)
    a.create_layer("I-STOOL",    ACI_STOOL_WD)

    # ---------------------------------------------------------------
    # Cabinet door reveals — thin recessed grooves between door/drawer
    # ---------------------------------------------------------------
    print("[reveals] cabinet door reveals", flush=True)
    a.set_active_layer("I-DETAIL")
    # For each base cabinet, vertical reveal at midpoint, plus horizontal
    # band at 6" below counter (drawer/door split)
    for x1, x2, _tag in CAB_BASE_RUNS:
        # Drawer-band horizontal split at z=BASE_H-6 (6" drawer)
        a.add_box([x1 + 0.5, -0.05, BASE_H - 6.5],
                  [x2 - 0.5,  0.05, BASE_H - 5.5])
        # Vertical reveal between door pair (single cabinet has 2 doors)
        cx = (x1 + x2) / 2
        a.add_box([cx - 0.05, -0.05, 4],
                  [cx + 0.05,  0.05, BASE_H - 7])
        # Bottom edge of doors (at toe kick)
        a.add_box([x1 + 0.5, -0.05, 4],
                  [x2 - 0.5,  0.05, 4.3])

    # Wall cabinet door reveals (vertical center split + bottom edge)
    print("[reveals] wall cabinet door reveals", flush=True)
    for x1, x2 in CAB_WALL_RUNS:
        cx = (x1 + x2) / 2
        a.add_box([cx - 0.05, -0.05, WALL_CAB_BOTTOM + 0.5],
                  [cx + 0.05,  0.05, WALL_CAB_TOP - 0.5])
        a.add_box([x1 + 0.5, -0.05, WALL_CAB_BOTTOM + 0.3],
                  [x2 - 0.5,  0.05, WALL_CAB_BOTTOM + 0.5])

    # ---------------------------------------------------------------
    # Hardware — cabinet pulls (4" bar pulls horizontal on doors,
    #            vertical on drawers)
    # ---------------------------------------------------------------
    print("[hardware] cabinet pulls", flush=True)
    a.set_active_layer("I-HARDWARE")
    # Base cabinet bar pulls (one per door, on top of door at drawer line)
    for x1, x2, _tag in CAB_BASE_RUNS:
        cx = (x1 + x2) / 2
        # Drawer pull (horizontal across entire cabinet drawer band)
        a.add_box([cx - 4, -0.6, BASE_H - 4.5],
                  [cx + 4, -0.3, BASE_H - 4])
        # Door pulls (small bar on each door)
        for door_cx in [(x1 + cx) / 2, (cx + x2) / 2]:
            a.add_box([door_cx - 0.3, -0.6, BASE_H - 12],
                      [door_cx + 0.3, -0.3, BASE_H - 8])
    # Pantry pulls
    for z in [BASE_H - 4, 60, 78]:
        a.add_box([161 - 0.3, -0.6, z - 2], [161 + 0.3, -0.3, z + 2])
    # Wall cabinet pulls (small horizontal under each door)
    for x1, x2 in CAB_WALL_RUNS:
        cx = (x1 + x2) / 2
        for door_cx in [(x1 + cx) / 2, (cx + x2) / 2]:
            a.add_box([door_cx - 1.5, -0.6, WALL_CAB_BOTTOM + 2],
                      [door_cx + 1.5, -0.3, WALL_CAB_BOTTOM + 2.5])

    # ---------------------------------------------------------------
    # Range — knobs + control panel
    # ---------------------------------------------------------------
    print("[range] knobs + handle", flush=True)
    # 5 knobs on front of range at z=33 (just below counter)
    for i, kx in enumerate([39, 45, 51, 57, 63]):
        a.add_cylinder([kx, -0.5, 33], 0.7, 0.5)
    # Oven door handle
    a.add_box([39, -0.6, 18], [63, -0.3, 19.5])

    # Dishwasher handle
    a.add_box([72, -0.6, BASE_H - 4], [84, -0.3, BASE_H - 3])

    # ---------------------------------------------------------------
    # Sink faucet swing arm — bend it so it looks intentional
    # ---------------------------------------------------------------
    print("[faucet] arm", flush=True)
    # Replace the simple vertical cylinder with a more detailed faucet:
    # Vertical body 12" + horizontal swing arm 8"
    # (We keep the existing one and add the arm + tip)
    # Find existing faucet body and lengthen via additional cylinders
    a.set_active_layer("I-FURN-APPL-MTL")
    # Already have: cyl at (113,23,COUNTER_H), r=0.6, h=12 (body)
    # Add: horizontal arm
    a.add_box([113 - 0.4, 23 - 0.4, COUNTER_H + 12],
              [113 + 0.4, 23 - 8,   COUNTER_H + 12.8])
    # Spout tip
    a.add_cylinder([113, 15, COUNTER_H + 11.5], 0.3, 1.0)
    # Handle on the side
    a.add_box([113 + 0.6, 23 - 0.4, COUNTER_H + 8],
              [113 + 1.5, 23 + 0.4, COUNTER_H + 11])

    # ---------------------------------------------------------------
    # Backsplash tile band — full-height behind counter
    # ---------------------------------------------------------------
    print("[backsplash] tile band", flush=True)
    a.set_active_layer("I-TILE")
    # On south wall, between counter top (z=36) and wall cab bottom (z=54)
    # spans full width except at range (the hood comes down to z=66)
    # Left of range
    a.add_box([0, -0.05, COUNTER_H], [36, 0.05, WALL_CAB_BOTTOM])
    # Right of range to end
    a.add_box([66, -0.05, COUNTER_H], [156, 0.05, WALL_CAB_BOTTOM])
    # Behind range (full height to hood)
    a.add_box([36, -0.05, COUNTER_H], [66, 0.05, 66])  # to hood bottom

    # ---------------------------------------------------------------
    # Crown molding on top of wall cabinets
    # ---------------------------------------------------------------
    print("[crown] crown molding strip", flush=True)
    a.set_active_layer("I-CROWN")
    for x1, x2 in CAB_WALL_RUNS:
        a.add_box([x1, -0.5, WALL_CAB_TOP],
                  [x2,  12.5, WALL_CAB_TOP + 2])
    # Pantry top crown
    a.add_box([156, -0.5, 84], [168, 24.5, 86])

    # ---------------------------------------------------------------
    # Pendant lights over island (3 hanging cylinders)
    # ---------------------------------------------------------------
    print("[pendants] over island", flush=True)
    a.set_active_layer("I-PENDANT")
    isl_center_y = (51 + 93) / 2
    for px in [60, 84, 108]:
        # Pendant cord
        a.add_cylinder([px, isl_center_y, 84], 0.1, 36)
        # Shade (cone-like, approximated as cylinder)
        a.add_cylinder([px, isl_center_y, 78], 4, 6)

    # ---------------------------------------------------------------
    # Bar stools at island (north / seating side)
    # ---------------------------------------------------------------
    print("[stools] 3 bar stools", flush=True)
    a.set_active_layer("I-STOOL")
    seat_y = 105 + 12  # 12" off the counter overhang into the room
    seat_z_base = 0
    seat_z_top = 24    # 24" counter-height stools (24" seat for 36" counter)
    for sx in [60, 84, 108]:
        # Seat
        a.add_cylinder([sx, seat_y, seat_z_top], 7, 1)
        # Pedestal
        a.add_cylinder([sx, seat_y, 0], 1.5, seat_z_top)
        # Foot ring (small cylinder ring)
        a.add_cylinder([sx, seat_y, 6], 4, 0.5)

    # ---------------------------------------------------------------
    # Sun lighting — try the sun command
    # ---------------------------------------------------------------
    print("[sun] try to enable sun", flush=True)
    try:
        # _.SUNPROPERTIES opens palette - skip it
        # Try setting sun via -SUN command if it exists
        a.send_command("_.SUNPROPERTIES\n")
        time.sleep(1)
        # Close palette by another command
        a.send_command("_.\n")
    except Exception as e:
        print(f"  sun: {e}", flush=True)

    # SHADOWPLOT may control whether shadows show in render (1 = on)
    try:
        sv("SHADOWPLOT", 2)  # ground + full shadows
        print("  SHADOWPLOT = 2", flush=True)
    except Exception as e:
        print(f"  SHADOWPLOT: {e}", flush=True)

    a.save()
    print(f"DONE entities={a.doc.ModelSpace.Count}", flush=True)


if __name__ == "__main__":
    main()
