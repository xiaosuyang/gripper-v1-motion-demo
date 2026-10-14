# -*- coding: utf-8 -*-
"""用 OpenCascade(OCP) 把 STEP 按运动分组三角化并写二进制 STL。"""
import json, os, struct, time, math
from OCP.STEPControl import STEPControl_Reader
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_FACE, TopAbs_REVERSED
from OCP.TopoDS import TopoDS
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, '..', 'stl')
os.makedirs(OUT, exist_ok=True)
LIN = float(os.environ.get('LIN', '0.18'))     # 线性弦高 mm
ANG = float(os.environ.get('ANG', '0.5'))      # 角偏差 rad

groups = json.load(open(os.path.join(HERE, 'groups.json')))

def _call(mod, names, *a):
    for n in names:
        if hasattr(mod, n):
            return getattr(mod, n)(*a)
    raise AttributeError(names)

def solid_bbox(shape):
    b = Bnd_Box()
    _call(BRepBndLib, ('Add_s','Add'), shape, b, True)
    pmin, pmax = b.CornerMin(), b.CornerMax()
    return (pmin.X(), pmax.X(), pmin.Y(), pmax.Y(), pmin.Z(), pmax.Z())

def match(bb):
    best, bd = None, 1e9
    for e in groups:
        g = e['bb']
        d = max(abs(bb[i]-g[i]) for i in range(6))
        if d < bd:
            bd, best = d, e['g']
    return (best, bd) if bd < 0.6 else (None, bd)

t0 = time.time()
rd = STEPControl_Reader()
rd.ReadFile(os.path.join(HERE, 'assy.step'))
rd.TransferRoots()
shape = rd.OneShape()
print('read %.0fs' % (time.time()-t0), flush=True)

solids = []
ex = TopExp_Explorer(shape, TopAbs_SOLID)
while ex.More():
    solids.append(_call(TopoDS, ('Solid_s','Solid'), ex.Current()))
    ex.Next()
print('solids:', len(solids), flush=True)

buckets = {g: [] for g in ('shell', 'frame', 'elec', 'left', 'right', 'gear')}
unmatched = 0
for s in solids:
    bb = solid_bbox(s)
    g, d = match(bb)
    if g is None:
        unmatched += 1
        continue
    buckets[g].append(s)
print('unmatched:', unmatched, {k: len(v) for k, v in buckets.items()}, flush=True)

def tessellate(shp):
    BRepMesh_IncrementalMesh(shp, LIN, False, ANG, True)
    tris = []
    exf = TopExp_Explorer(shp, TopAbs_FACE)
    while exf.More():
        face = _call(TopoDS, ('Face_s','Face'), exf.Current())
        loc = TopLoc_Location()
        tri = None
        tri = _call(BRep_Tool, ('Triangulation_s','Triangulation'), face, loc)
        if tri is not None:
            trsf = loc.Transformation()
            nn = tri.NbNodes()
            pts = [None]
            for i in range(1, nn+1):
                p = tri.Node(i).Transformed(trsf)
                pts.append((p.X(), p.Y(), p.Z()))
            rev = (face.Orientation() == TopAbs_REVERSED)
            for i in range(1, tri.NbTriangles()+1):
                t = tri.Triangle(i)
                a, b, c = t.Value(1), t.Value(2), t.Value(3)
                if rev:
                    b, c = c, b
                tris.append((pts[a], pts[b], pts[c]))
        exf.Next()
    return tris

def write_stl(path, tris):
    n = len(tris)
    with open(path, 'wb') as f:
        f.write(b'\0'*80)
        f.write(struct.pack('<I', n))
        for (a, b, c) in tris:
            ux, uy, uz = b[0]-a[0], b[1]-a[1], b[2]-a[2]
            vx, vy, vz = c[0]-a[0], c[1]-a[1], c[2]-a[2]
            nx, ny, nz = uy*vz-uz*vy, uz*vx-ux*vz, ux*vy-uy*vx
            L = math.sqrt(nx*nx+ny*ny+nz*nz) or 1.0
            f.write(struct.pack('<3f', nx/L, ny/L, nz/L))
            for p in (a, b, c):
                f.write(struct.pack('<3f', p[0], p[1], p[2]))
            f.write(struct.pack('<H', 0))
    return n

total = 0
for g, lst in buckets.items():
    if not lst:
        continue
    t1 = time.time()
    tris = []
    for s in lst:
        tris += tessellate(s)
    n = write_stl(os.path.join(OUT, g+'.stl'), tris)
    total += n
    print('%-6s solids=%2d tris=%7d %5.2fMB %.0fs' %
          (g, len(lst), n, os.path.getsize(os.path.join(OUT, g+'.stl'))/1e6, time.time()-t1), flush=True)
print('TOTAL tris %d  %.0fs' % (total, time.time()-t0), flush=True)
