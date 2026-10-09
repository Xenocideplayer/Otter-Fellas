"""Read and write Timberborn .timbermesh files (zlib-wrapped protobuf-net, schema from Timberborn.TimbermeshDTO).

Model{1 Version int, 2 Name str, 3 Nodes Node[]}
Node{1 Parent int, 2 Name, 3 Position V3, 4 Rotation Q, 5 Scale V3, 6 VertexCount, 7 VertexProperties VP[],
     8 Meshes Mesh[], 9 VertexAnimations VA[], 10 NodeAnimations NA[]}
Mesh{1 Indices int[] (packed or not), 2 Material str}
VP{1 Name, 2 ScalarType enum, 3 ScalarTypeDimension, 4 Data bytes}
VA{1 Name, 2 Framerate float, 3 AnimatedVertexCount int, 4 Frames VAF[]}   VAF{1 VertexProperties VP[]}
NA{1 Name, 2 Framerate, 3 Frames NAF[]}   NAF{1 Position V3, 2 Rotation Q, 3 Scale V3}
V3{1 X,2 Y,3 Z float}  Q{1 X,2 Y,3 Z,4 W float}
"""
import struct
import zlib
from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np


# ---------------------------------------------------------------- wire helpers
def _varint(buf, i):
    r = 0
    s = 0
    while True:
        b = buf[i]
        i += 1
        r |= (b & 0x7F) << s
        if b < 0x80:
            return r, i
        s += 7


def _fields(buf):
    i, n = 0, len(buf)
    mv = memoryview(buf)
    while i < n:
        key, i = _varint(buf, i)
        fn, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(buf, i)
        elif wt == 1:
            v = bytes(mv[i:i + 8]); i += 8
        elif wt == 2:
            ln, i = _varint(buf, i)
            v = mv[i:i + ln]; i += ln
        elif wt == 5:
            v = bytes(mv[i:i + 4]); i += 4
        else:
            raise ValueError(f"wire type {wt}")
        yield fn, wt, v


def _signed32(v):
    v &= 0xFFFFFFFFFFFFFFFF
    if v >= 1 << 63:
        v -= 1 << 64
    return v


def _f32(v):
    return struct.unpack("<f", v)[0]


def _enc_varint(v):
    if v < 0:
        v += 1 << 64
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            return bytes(out)


def _key(fn, wt):
    return _enc_varint((fn << 3) | wt)


def _ld(fn, payload):
    return _key(fn, 2) + _enc_varint(len(payload)) + payload


def _str(fn, s):
    return _ld(fn, s.encode("utf-8")) if s is not None else b""


def _int(fn, v):
    return _key(fn, 0) + _enc_varint(v) if v else b""


def _float(fn, v):
    return _key(fn, 5) + struct.pack("<f", v) if v != 0.0 else b""


# ---------------------------------------------------------------- model classes
@dataclass
class VertexProperty:
    name: str
    scalar_type: int  # 4 = Float
    dimension: int
    data: bytes

    def array(self):
        assert self.scalar_type == 4, self.scalar_type
        return np.frombuffer(self.data, dtype="<f4").reshape(-1, self.dimension)

    @staticmethod
    def from_array(name, arr):
        arr = np.ascontiguousarray(arr, dtype="<f4")
        return VertexProperty(name, 4, arr.shape[1], arr.tobytes())

    def encode(self):
        return _str(1, self.name) + _int(2, self.scalar_type) + _int(3, self.dimension) + (_ld(4, self.data) if self.data else b"")


@dataclass
class MeshPart:
    indices: np.ndarray
    material: str

    def encode(self):
        packed = b"".join(_enc_varint(int(x)) for x in self.indices)
        return _ld(1, packed) + _str(2, self.material)


@dataclass
class VertexAnimation:
    name: str
    framerate: float
    animated_vertex_count: int
    frames: List[List[VertexProperty]]

    def encode(self):
        out = _str(1, self.name) + _float(2, self.framerate) + _int(3, self.animated_vertex_count)
        for fr in self.frames:
            out += _ld(4, b"".join(_ld(1, p.encode()) for p in fr))
        return out


@dataclass
class NodeAnimation:
    name: str
    framerate: float
    frames: list  # list of (pos(3), rot(4), scale(3)) raw encoded bytes per frame

    def encode(self):
        return _str(1, self.name) + _float(2, self.framerate) + b"".join(_ld(3, f) for f in self.frames)


@dataclass
class Node:
    parent: int
    name: str
    position: tuple
    rotation: tuple
    scale: tuple
    vertex_count: int = 0
    vertex_properties: List[VertexProperty] = field(default_factory=list)
    meshes: List[MeshPart] = field(default_factory=list)
    vertex_animations: List[VertexAnimation] = field(default_factory=list)
    node_animations: List[NodeAnimation] = field(default_factory=list)

    def prop(self, name) -> Optional[VertexProperty]:
        for p in self.vertex_properties:
            if p.name == name:
                return p
        return None

    def encode(self):
        out = _int(1, self.parent) if self.parent != 0 else b""
        out += _str(2, self.name)
        out += _ld(3, b"".join(_float(i + 1, v) for i, v in enumerate(self.position)))
        out += _ld(4, b"".join(_float(i + 1, v) for i, v in enumerate(self.rotation)))
        out += _ld(5, b"".join(_float(i + 1, v) for i, v in enumerate(self.scale)))
        out += _int(6, self.vertex_count)
        out += b"".join(_ld(7, p.encode()) for p in self.vertex_properties)
        out += b"".join(_ld(8, m.encode()) for m in self.meshes)
        out += b"".join(_ld(9, a.encode()) for a in self.vertex_animations)
        out += b"".join(_ld(10, a.encode()) for a in self.node_animations)
        return out


@dataclass
class Model:
    version: int
    name: str
    nodes: List[Node]

    def encode(self):
        return _int(1, self.version) + _str(2, self.name) + b"".join(_ld(3, n.encode()) for n in self.nodes)


# ---------------------------------------------------------------- decoding
def _vec(buf, n):
    vals = [0.0] * n
    for fn, wt, v in _fields(buf):
        vals[fn - 1] = _f32(v)
    return tuple(vals)


def _vp(buf):
    name, st, dim, data = "", 0, 0, b""
    for fn, wt, v in _fields(buf):
        if fn == 1: name = bytes(v).decode()
        elif fn == 2: st = v
        elif fn == 3: dim = v
        elif fn == 4: data = bytes(v)
    return VertexProperty(name, st, dim, data)


def _mesh(buf):
    idx = []
    mat = ""
    for fn, wt, v in _fields(buf):
        if fn == 1:
            if wt == 2:
                b = bytes(v); i = 0
                while i < len(b):
                    x, i = _varint(b, i); idx.append(x)
            else:
                idx.append(v)
        elif fn == 2:
            mat = bytes(v).decode()
    return MeshPart(np.array(idx, dtype=np.int64), mat)


def _va(buf):
    name, fr, avc, frames = "", 0.0, 0, []
    for fn, wt, v in _fields(buf):
        if fn == 1: name = bytes(v).decode()
        elif fn == 2: fr = _f32(v)
        elif fn == 3: avc = v
        elif fn == 4: frames.append([_vp(bytes(p)) for f2, w2, p in _fields(bytes(v)) if f2 == 1])
    return VertexAnimation(name, fr, avc, frames)


def _na(buf):
    name, fr, frames = "", 0.0, []
    for fn, wt, v in _fields(buf):
        if fn == 1: name = bytes(v).decode()
        elif fn == 2: fr = _f32(v)
        elif fn == 3: frames.append(bytes(v))
    return NodeAnimation(name, fr, frames)


def decode_naf(raw):
    pos, rot, sc = (0.0,) * 3, (0.0,) * 4, (0.0,) * 3
    for fn, wt, v in _fields(raw):
        if fn == 1: pos = _vec(bytes(v), 3)
        elif fn == 2: rot = _vec(bytes(v), 4)
        elif fn == 3: sc = _vec(bytes(v), 3)
    return pos, rot, sc


def _node(buf):
    n = Node(0, "", (0, 0, 0), (0, 0, 0, 1), (1, 1, 1))
    for fn, wt, v in _fields(buf):
        if fn == 1: n.parent = _signed32(v)
        elif fn == 2: n.name = bytes(v).decode()
        elif fn == 3: n.position = _vec(bytes(v), 3)
        elif fn == 4: n.rotation = _vec(bytes(v), 4)
        elif fn == 5: n.scale = _vec(bytes(v), 3)
        elif fn == 6: n.vertex_count = v
        elif fn == 7: n.vertex_properties.append(_vp(bytes(v)))
        elif fn == 8: n.meshes.append(_mesh(bytes(v)))
        elif fn == 9: n.vertex_animations.append(_va(bytes(v)))
        elif fn == 10: n.node_animations.append(_na(bytes(v)))
    return n


def read(path) -> Model:
    raw = open(path, "rb").read()
    assert raw[:2] == b"\x78\x9c", "not a zlib timbermesh"
    buf = zlib.decompress(raw)
    m = Model(0, "", [])
    for fn, wt, v in _fields(buf):
        if fn == 1: m.version = v
        elif fn == 2: m.name = bytes(v).decode()
        elif fn == 3: m.nodes.append(_node(bytes(v)))
    return m


def write(model: Model, path):
    # The game checks for the 0x78 0x9C zlib header then inflates with DeflateStream.
    data = zlib.compress(model.encode(), 9)
    data = b"\x78\x9c" + data[2:]
    open(path, "wb").write(data)
