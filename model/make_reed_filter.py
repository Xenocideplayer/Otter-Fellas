"""Reed Filter model: the Folktails water pump with clumps of the game's own cattails around its base.
usage: python3 make_reed_filter.py WaterPump.Folktails.Model.timbermesh CattailMature.timbermesh out.timbermesh"""
import math
import sys
import timbermesh as tm

pump_path, cattail_path, out = sys.argv[1:4]
pump = tm.read(pump_path)
cat = [n for n in tm.read(cattail_path).nodes if n.vertex_count][0]

# Reed clumps ringed around the tank (centre (1, 1), radius ~0.75), leaving the entrance side (around
# angle -60 deg, towards (1.35, 0.36)) and the pipe side (towards z = 2.5) open.
# (angle around the tank in degrees, distance from tank centre, scale, yaw)
CLUMPS = [(150, 0.92, 0.62, 10), (185, 0.95, 0.68, 80), (215, 0.9, 0.58, 160), (250, 0.88, 0.6, 230),
          (20, 0.92, 0.6, 300), (45, 0.95, 0.56, 40), (115, 0.9, 0.5, 120), (-15, 0.9, 0.55, 200)]
HALF = 0.5  # the cattail clump spans about 0..1.0 in x and z before scaling; rotate around its middle


def yaw(deg):
    a = math.radians(deg) / 2
    return (0.0, math.sin(a), 0.0, math.cos(a))


def rotate_y(v, deg):
    a = math.radians(deg)
    # Unity is left-handed: a positive rotation about +Y turns +X towards -Z
    return (v[0] * math.cos(a) + v[2] * math.sin(a), v[1], -v[0] * math.sin(a) + v[2] * math.cos(a))


for i, (ang, dist, s, deg) in enumerate(CLUMPS):
    cx = 1.0 + dist * math.cos(math.radians(ang))
    cz = 1.0 + dist * math.sin(math.radians(ang))
    off = rotate_y((HALF * s, 0.0, HALF * s), deg)
    node = tm.Node(0, f"Reeds{i}", (cx - off[0], -0.03, cz - off[2]), yaw(deg), (s, s * 1.1, s))
    node.vertex_count = cat.vertex_count
    node.vertex_properties = list(cat.vertex_properties)
    node.meshes = [tm.MeshPart(m.indices, m.material) for m in cat.meshes]
    pump.nodes.append(node)

tm.write(pump, out)
print("nodes", len(pump.nodes))
