"""Timber Tunnels: the otters' wooden take on the Iron Teeth tubeway set, built from scratch in the Folktails
materials: slatted log tubes held by hoops, with little lanterns that light up while otters are passing through
(the game hides travellers inside tubes and lights the tube's lamps instead).

Writes, for the game's TubeModel (variant names are <down><left><up><right><top><bottom>, 1 = connected; down = the
front edge, z = 0; left = x = 0; up = the back edge, z = 1; right = x = 1):
  TimberTunnel<code>.Otters.Model.timbermesh         12 variants for the tunnel (same set as the Tubeway)
  TimberShaft<code>.Otters.Model.timbermesh          24 variants for the vertical shaft (same set as the Vertical Tubeway)
  TimberShaftCover.Otters.Model.timbermesh           the deck on top of a shaft (#Platform)
  SealedTimberTunnel.Otters.Model.timbermesh         the watertight block tunnel (straight, front to back)
  TunnelLodge.Otters.Model.timbermesh                the 3 x 2 station (a log rotunda with a thatched roof, a clock
                                                      hand node #HandOtter, tunnel mouths at both sides)
  + ConstructionStage0 models for the sealed tunnel and the station (tunnel and shaft keep the Tubeway's)
usage: python3 make_tunnels.py out_dir
"""
import math
import os
import sys

import numpy as np

import procmesh as pm
import timbermesh as tm

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)

LIGHT = "BaseWood_LightBrown.Folktails"
BROWN = "BaseWood_Brown.Folktails"
WHITE = "BaseWood_White.Folktails"
PLANKS = "IrregularPlanks_Brown.Folktails"
THATCH = "ThatchedRoof.Folktails"
WINDOWS = "WindowsAtlas.Folktails"
ROPE = (0.80, 0.70, 0.50, 1)
TEAL = (0.30, 0.55, 0.62, 1)

TUNNEL_VARIANTS = ["000000", "000001", "001000", "001001", "001100", "001101", "011100", "011101", "101000",
                   "101001", "111100", "111101"]
SHAFT_VARIANTS = ["000000", "000001", "000010", "000011", "001000", "001001", "001010", "001011", "001100", "001101",
                  "001110", "001111", "011100", "011101", "011110", "011111", "101000", "101001", "101010", "101011",
                  "111100", "111101", "111110", "111111"]

# tunnel cross-section (matches the Tubeway's collider: 0.36 wide, 0.74 tall, floor at 0.04)
HALF_W = 0.19
WALL_TOP = 0.40
ARCH = 0.37
FLOOR = 0.04
# direction -> unit vector in model space (x, z)
DIRS = {"down": (0.0, -1.0), "left": (-1.0, 0.0), "up": (0.0, 1.0), "right": (1.0, 0.0)}
ORDER = ["down", "left", "up", "right"]
CENTRE = np.array([0.5, 0.0, 0.5])


def profile(n=9):
    """Points round the tunnel's inside (lateral u, height v), from the left foot over the arch to the right foot."""
    pts = [(-HALF_W, FLOOR)]
    for i in range(n + 1):
        t = math.pi * (1 - i / n)
        pts.append((HALF_W * math.cos(t), WALL_TOP + ARCH * math.sin(t)))
    pts.append((HALF_W, FLOOR))
    return pts


PROFILE = profile()
SLAT_AT = [(-HALF_W, 0.16), (-HALF_W, 0.32)] + \
          [(HALF_W * math.cos(math.radians(a)), WALL_TOP + ARCH * math.sin(math.radians(a))) for a in (155, 118, 90, 62, 25)] + \
          [(HALF_W, 0.32), (HALF_W, 0.16)]


def frame(d):
    """Unit along-vector, lateral vector and up for a horizontal direction (x, z)."""
    a = np.array([d[0], 0.0, d[1]])
    side = np.array([-d[1], 0.0, d[0]])
    return a, side, np.array([0.0, 1.0, 0.0])


def hoop(m, origin, d, thick=0.035, depth=0.045, color=(1, 1, 1, 1)):
    """A wooden hoop round the tunnel at origin (a point on the tunnel axis at floor level)."""
    a, side, up = frame(d)
    for (u0, v0), (u1, v1) in zip(PROFILE[:-1], PROFILE[1:]):
        p0 = origin + side * u0 * 1.08 + up * v0
        p1 = origin + side * u1 * 1.08 + up * v1
        _band(m, p0, p1, a, thick, depth, color)


def _band(m, p0, p1, along, thick, depth, color):
    """A flat strip from p0 to p1, `depth` wide along the tunnel and `thick` thick."""
    p0 = np.asarray(p0, float); p1 = np.asarray(p1, float)
    e = p1 - p0
    L = np.linalg.norm(e)
    if L < 1e-6:
        return
    e /= L
    n = np.cross(along, e); n /= np.linalg.norm(n)
    R = np.stack([along, n, e], axis=1)    # local x = along, y = outwards, z = along the strip
    pm.box(m, BROWN, (-depth / 2, -thick / 2, 0.0), (depth / 2, thick / 2, L), color, rot=R, pivot=np.zeros(3), offset=p0)


def slats(m, start, end, d):
    """Boards along the tunnel between two points on its axis."""
    a, side, up = frame(d)
    for u, v in SLAT_AT:
        p0 = start + side * u + up * v
        p1 = end + side * u + up * v
        pm.beam(m, LIGHT, p0, p1, 0.055, 0.022)


def floor_boards(m, start, end, d):
    a, side, up = frame(d)
    L = np.linalg.norm(end - start)
    if L < 1e-6:
        return
    R = np.stack([side, up, a], axis=1)
    pm.box(m, PLANKS, (-HALF_W - 0.02, FLOOR - 0.025, 0.0), (HALF_W + 0.02, FLOOR + 0.005, L), rot=R,
           pivot=np.zeros(3), offset=start)


def arm(m, d, from_centre=0.0):
    """The half of a tunnel from the tile's centre to its edge in direction d."""
    a, side, up = frame(d)
    start = CENTRE + a * from_centre
    end = CENTRE + a * 0.5
    floor_boards(m, start, end, d)
    slats(m, start, end, d)
    hoop(m, CENTRE + a * 0.22, d)
    hoop(m, CENTRE + a * 0.47, d, thick=0.045, depth=0.06)        # a collar where it meets the next tile
    rope = CENTRE + a * 0.47 + up * (WALL_TOP + ARCH + 0.03)
    pm.cylinder(m, WHITE, rope - a * 0.03, rope + a * 0.03, 0.03, seg=6, color=ROPE)
    lantern(m, CENTRE + a * 0.22 + side * (HALF_W + 0.05) + up * (WALL_TOP + 0.05))


def lantern(m, p):
    """A small lamp hung on the tunnel's side (window material: lit while otters travel through)."""
    p = np.asarray(p, float)
    pm.box(m, WINDOWS, p - (0.03, 0.04, 0.03), p + (0.03, 0.04, 0.03))
    pm.box(m, BROWN, p + (-0.04, 0.04, -0.04), p + (0.04, 0.06, 0.04))


def end_wall(m, d):
    """Planked end of a dead-end tunnel, facing direction d (the tunnel runs the other way)."""
    a, side, up = frame(d)
    for k in range(5):
        u0 = -HALF_W + k * 2 * HALF_W / 5
        u1 = u0 + 2 * HALF_W / 5 - 0.008
        top = max(WALL_TOP + ARCH * math.sqrt(max(0.0, 1 - ((u0 + u1) / 2 / HALF_W) ** 2)), FLOOR)
        R = np.stack([side, up, a], axis=1)
        pm.box(m, PLANKS, (u0, FLOOR, -0.02), (u1, top, 0.02), rot=R, pivot=np.zeros(3), offset=CENTRE + a * 0.02)
    hoop(m, CENTRE + a * 0.02, d, thick=0.05, depth=0.06)


def hub(m, n_conn):
    """Where tunnels meet: a lid over the crossing and corner posts."""
    pm.cylinder(m, PLANKS, (0.5, WALL_TOP + ARCH - 0.02, 0.5), (0.5, WALL_TOP + ARCH + 0.03, 0.5), 0.25, seg=8)
    pm.cone(m, THATCH, (0.5, WALL_TOP + ARCH + 0.03, 0.5), 0.12, 0.27, seg=8)
    for dx in (-1, 1):
        for dz in (-1, 1):
            pm.cylinder(m, BROWN, (0.5 + dx * 0.215, 0.0, 0.5 + dz * 0.215), (0.5 + dx * 0.215, WALL_TOP + ARCH, 0.5 + dz * 0.215),
                        0.03, seg=6)


def deck(m):
    """The thin plank pad under every tile (the Tubeway has one too)."""
    for i in range(4):
        z0 = 0.01 + i * 0.245
        pm.box(m, LIGHT, (0.01, 0.0, z0), (0.99, 0.035, z0 + 0.235), uv_offset=(0.1 * i, 0.2 * i))


def shaft(m, y0, y1, cap=False, rungs=True):
    """A vertical slatted barrel at the tile's centre, with ladder rungs inside."""
    r = 0.2
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        x, z = 0.5 + math.cos(a) * r, 0.5 + math.sin(a) * r
        pm.beam(m, LIGHT, (x, y0, z), (x, y1, z), 0.055, 0.022)
    yy = y0 + 0.08
    while yy < y1 - 0.02:
        pm.cylinder(m, BROWN, (0.5, yy, 0.5), (0.5, yy + 0.04, 0.5), r + 0.022, seg=12, caps=False)
        yy += 0.32
    if rungs:
        yy = y0 + 0.12
        while yy < y1 - 0.05:
            pm.cylinder(m, BROWN, (0.36, yy, 0.62), (0.64, yy, 0.62), 0.014, seg=5)
            yy += 0.16
    if cap:
        pm.cylinder(m, PLANKS, (0.5, y1 - 0.02, 0.5), (0.5, y1 + 0.03, 0.5), r + 0.04, seg=10)
        pm.cone(m, THATCH, (0.5, y1 + 0.03, 0.5), 0.1, r + 0.06, seg=10)     # top at y1 + 0.13 (under 0.98)


def tunnel_variant(code, vertical=False):
    conn = [ORDER[i] for i in range(4) if code[i] == "1"]
    top, bottom = code[4] == "1", code[5] == "1"
    m = pm.Mesh()
    deck(m)
    if not conn and not top and not bottom:
        conn_draw = ["down", "up"]                     # a lone piece: straight, front to back
    else:
        conn_draw = conn
    for d in conn_draw:
        arm(m, DIRS[d])
    straight = sorted(conn_draw) in (["down", "up"], ["left", "right"])
    if len(conn_draw) == 1 and not (top or bottom):
        end_wall(m, (-DIRS[conn_draw[0]][0], -DIRS[conn_draw[0]][1]))
    elif len(conn_draw) >= 2 and not straight:
        hub(m, len(conn_draw))
    if vertical:
        if top or bottom:
            shaft(m, 0.0 if bottom else FLOOR, 1.0 if top else 0.84, cap=not top)
    elif bottom:
        shaft(m, 0.0, 0.84, cap=True)          # the tunnel climbs in from a shaft below; capped inside the cell
    return m


def write_model(name, m, extra_nodes=()):
    model = pm.single_node_model(name, m, extra_nodes)
    path = os.path.join(out_dir, name + ".Model.timbermesh")
    tm.write(model, path)
    return path


def shaft_cover():
    m = pm.Mesh()
    for i in range(5):
        x0 = 0.01 + i * 0.196
        pm.box(m, LIGHT, (x0, 0.92, 0.0), (x0 + 0.188, 0.98, 1.0), uv_offset=(0.13 * i, 0.0))
    for z in (0.06, 0.94):
        pm.box(m, BROWN, (0.0, 0.88, z - 0.04), (1.0, 0.92, z + 0.04))
    return m


def sealed(stage0=False):
    """Watertight: a timber box round a straight tunnel, caulked with tar-dark seams."""
    m = pm.Mesh()
    deck(m)
    if stage0:
        for x in (0.06, 0.94):
            for z in (0.06, 0.94):
                pm.box(m, BROWN, (x - 0.05, 0.0, z - 0.05), (x + 0.05, 0.5, z + 0.05))
        return m
    for side in (0, 1):
        x = 0.02 if side == 0 else 0.98
        for k in range(6):
            y0 = 0.04 + k * 0.16
            pm.box(m, PLANKS, (x - 0.02, y0, 0.0), (x + 0.02, y0 + 0.15, 1.0), uv_offset=(0.0, 0.17 * k))
    for k in range(5):
        x0 = 0.02 + k * 0.192
        pm.box(m, PLANKS, (x0, 0.96, 0.0), (x0 + 0.188, 1.0, 1.0), uv_offset=(0.2 * k, 0.0))
    for z in (0.03, 0.97):
        for x in (0.03, 0.97):
            pm.box(m, BROWN, (x - 0.04, 0.0, z - 0.04), (x + 0.04, 1.0, z + 0.04))
        pm.box(m, BROWN, (0.0, 0.92, z - 0.03), (1.0, 1.0, z + 0.03))
        pm.box(m, BROWN, (0.0, 0.0, z - 0.03), (1.0, 0.06, z + 0.03))
    # the tunnel mouths showing at both ends
    for z, d in ((0.0, (0.0, -1.0)), (1.0, (0.0, 1.0))):
        hoop(m, np.array([0.5, 0.0, z]), d, thick=0.05, depth=0.05)
    return m


def station(stage0=False):
    """3 x 2: a round log hall with a thatched cone roof, door at the front middle, tunnel mouths left and right on
    both rows, and a clock over the door."""
    m = pm.Mesh()
    for i in range(10):                                                   # floor
        x0 = 0.02 + i * 0.296
        pm.box(m, LIGHT, (x0, 0.0, 0.02), (x0 + 0.286, 0.08, 1.98), uv_offset=(0.13 * i, 0.07 * i))
    c = np.array([1.5, 0.0, 1.0])
    R = 0.9
    if stage0:
        for k in range(12):
            a = 2 * math.pi * k / 12
            x, z = c[0] + math.cos(a) * R, c[2] + math.sin(a) * R
            pm.cylinder(m, BROWN, (x, 0.08, z), (x, 0.7 if k % 2 else 1.1, z), 0.06, seg=6)
        return m, []
    n = 16
    door = None
    for k in range(n):
        a0 = 2 * math.pi * k / n
        a1 = 2 * math.pi * (k + 1) / n
        mid = (a0 + a1) / 2
        p0 = c + np.array([math.cos(a0) * R, 0.0, math.sin(a0) * R])
        p1 = c + np.array([math.cos(a1) * R, 0.0, math.sin(a1) * R])
        facing = np.array([math.cos(mid), 0.0, math.sin(mid)])
        is_door = facing[2] < -0.95                                       # the front, towards z = 0
        is_mouth = abs(facing[0]) > 0.9                                   # left and right walls
        for j in range(6):                                                # log courses
            y = 0.14 + j * 0.15
            if (is_door or is_mouth) and y < 0.82:
                continue
            pm.cylinder(m, BROWN if j % 2 else LIGHT, p0 + (0, y, 0), p1 + (0, y, 0), 0.075, seg=7)
        if is_door:
            door = (p0, p1)
    # posts at the openings
    for k in range(n):
        a = 2 * math.pi * k / n
        p = c + np.array([math.cos(a) * R, 0.0, math.sin(a) * R])
        pm.cylinder(m, BROWN, p + (0, 0.08, 0), p + (0, 1.05, 0), 0.06, seg=6)
    # thatched cone roof with a log ring and a little lantern on top
    pm.cylinder(m, BROWN, c + (0, 1.0, 0), c + (0, 1.08, 0), R + 0.1, seg=n)
    pm.cone(m, THATCH, c + (0, 1.06, 0), 0.85, R + 0.2, seg=n)
    pm.cylinder(m, BROWN, c + (0, 1.85, 0), c + (0, 2.05, 0), 0.05, seg=6)
    pm.box(m, WINDOWS, (1.43, 1.95, 0.93), (1.57, 2.09, 1.07))
    pm.cone(m, THATCH, c + (0, 2.09, 0), 0.12, 0.12, seg=6)
    # tunnel mouths everywhere the station's nav edges join the tunnel network: left and right on both rows, the
    # three cells along the back and the two front corners. Corner cells get a little crossing.
    def stub(start, end, d):
        a, side, up = frame(d)
        floor_boards(m, start, end, d)
        slats(m, start, end, d)
        hoop(m, end - a * 0.03, d, thick=0.05, depth=0.06)
        hoop(m, start + a * 0.04, d, thick=0.05, depth=0.06)
    for z in (0.5, 1.5):
        for d, x_edge in (((-1.0, 0.0), 0.0), ((1.0, 0.0), 3.0)):
            wall_x = c[0] + d[0] * math.sqrt(max(0.0, R * R - (z - c[2]) ** 2)) * 0.97
            stub(np.array([wall_x, 0.0, z]), np.array([x_edge, 0.0, z]), d)
    for x in (0.5, 1.5, 2.5):                                            # back
        if x == 1.5:
            start = np.array([x, 0.0, c[2] + R * 0.97])
        else:
            start = np.array([x, 0.0, 1.5])
        stub(start, np.array([x, 0.0, 2.0]), (0.0, 1.0))
    for x in (0.5, 2.5):                                                 # front corners
        stub(np.array([x, 0.0, 0.5]), np.array([x, 0.0, 0.0]), (0.0, -1.0))
    for x in (0.5, 2.5):
        for z in (0.5, 1.5):
            pm.cylinder(m, PLANKS, (x, WALL_TOP + ARCH - 0.02, z), (x, WALL_TOP + ARCH + 0.03, z), 0.25, seg=8)
            pm.cone(m, THATCH, (x, WALL_TOP + ARCH + 0.03, z), 0.12, 0.27, seg=8)
    # door frame and lintel, a bench inside, a clock face over the door
    pm.box(m, BROWN, (1.15, 0.08, 0.06), (1.22, 0.85, 0.14))
    pm.box(m, BROWN, (1.78, 0.08, 0.06), (1.85, 0.85, 0.14))
    pm.box(m, BROWN, (1.10, 0.80, 0.04), (1.90, 0.90, 0.16))
    face_c = np.array([1.5, 1.22, 0.10])
    pm.cylinder(m, PLANKS, face_c + (0, 0, 0.02), face_c - (0, 0, 0.03), 0.2, seg=14)
    pm.cylinder(m, BROWN, face_c - (0, 0, 0.03), face_c - (0, 0, 0.045), 0.215, seg=14, caps=False)
    for k in range(4):
        a = math.pi / 2 * k
        p = face_c + np.array([math.cos(a) * 0.16, math.sin(a) * 0.16, -0.035])
        pm.box(m, WHITE, p - (0.015, 0.015, 0.005), p + (0.015, 0.015, 0.005), color=(0.95, 0.9, 0.8, 1))
    hand = pm.Mesh()                                                     # points up; the game turns it round z
    pm.box(hand, WHITE, (-0.012, -0.02, -0.01), (0.012, 0.15, 0.01), color=TEAL)
    pm.cylinder(hand, BROWN, (0, 0, -0.015), (0, 0, 0.012), 0.022, seg=8)
    hand_node = hand.node("#HandOtter")
    hand_node.position = (float(face_c[0]), float(face_c[1]), float(face_c[2] - 0.06))
    # a pennant on the roof, and lamps by the door
    pm.cylinder(m, BROWN, (0.35, 0.08, 0.2), (0.35, 1.6, 0.2), 0.03, seg=6)
    pm.triangle(m, WHITE, (0.35, 1.58, 0.2), (0.35, 1.36, 0.2), (0.75, 1.47, 0.2), color=TEAL)
    for x in (1.05, 1.95):
        pm.box(m, WINDOWS, (x - 0.05, 0.62, 0.02), (x + 0.05, 0.74, 0.1))
    return m, [hand_node]


written = []
for code in TUNNEL_VARIANTS:
    written.append(write_model(f"TimberTunnel{code}.Otters", tunnel_variant(code)))
for code in SHAFT_VARIANTS:
    written.append(write_model(f"TimberShaft{code}.Otters", tunnel_variant(code, vertical=True)))
written.append(write_model("TimberShaftCover.Otters", shaft_cover()))
written.append(write_model("SealedTimberTunnel.Otters", sealed()))
written.append(write_model("SealedTimberTunnel.Otters.ConstructionStage0", sealed(stage0=True)))
m, extra = station()
written.append(write_model("TunnelLodge.Otters", m, extra))
m, extra = station(stage0=True)
written.append(write_model("TunnelLodge.Otters.ConstructionStage0", m, extra))
print(len(written), "models")
