# -*- coding: utf-8 -*-
"""把力控夹爪 STEP 按运动分组导出二进制 STL，供网页动画使用。"""
import gmsh, re, sys, time, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'stl')
os.makedirs(OUT, exist_ok=True)
MESH_SIZE = float(sys.argv[1]) if len(sys.argv) > 1 else 3.5

def clean(n):
    n = re.sub(r'^Shapes/', '', n)
    n = re.sub(r'^装配体-左手/', '', n)
    n = re.sub(r'^NAUO\d+/', '', n)
    n = re.sub(r'~[A-Za-z0-9]{4}\.step$', '', n)
    return n

GROUPS = ['shell', 'frame', 'elec', 'left', 'right', 'gear']

def classify(name, bb):
    """bb = (xmin,xmax,ymin,ymax,zmin,zmax)"""
    cx = (bb[0] + bb[1]) / 2.0
    dx, dy, dz = bb[1]-bb[0], bb[3]-bb[2], bb[5]-bb[4]
    side = 'left' if cx < 0 else 'right'
    # 齿轮
    if name.startswith('0.5模齿轮'):
        return 'gear'
    # 运动件（手指 + 齿条 + 滑块 + 垫片 + 应变片）
    mv = {'0.5模齿条_SW零件', '力控夹爪前端1', '力控夹爪后端1', '力控夹爪盖',
          '夹爪前垫', '夹爪后垫', '中部橡胶垫', '应变片1', '薄m5', '夹爪后端夹紧盖'}
    if name in mv:
        return side
    # 无名滑块: 18.9 x 8.0 x 20.0, 位于导轨上方
    if name.strip() == '' and 15 < dx < 25 and 6 < dy < 10 and 15 < dz < 25 \
       and bb[2] < -4 and bb[3] < 0 and abs(bb[4]) > 5:
        return side
    # 半透明外壳与固定盖板
    if name in ('c-0821', 'd-0821', '齿条外盖', '齿轮 条盖'):
        return 'shell'
    # 电子/电机（静止）
    if name.startswith('TMZ-04') and dx > 40:
        return 'elec'
    if 'PRELAYOUT' in name and dx > 100:
        return 'elec'
    # 静止结构件
    fr = ('MGN导轨', '内法兰', '外法兰', '机械臂转接件1', '活动卡箍', '转接件夹爪端',
          '腕部相机支架', 'ID 壳a', 'ID 壳b', '腕部相机', '管夹套扳手', '管夹套杆', '管夹套螺母')
    if any(k in name for k in fr):
        return 'frame'
    # 无名中等实体（ID 壳镜片座等）归入 frame
    if name.strip() == '' and min(dx, dy, dz) > 4:
        return 'frame'
    return None

def run():
    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.option.setNumber('Mesh.MeshSizeMax', MESH_SIZE)
    gmsh.option.setNumber('Mesh.MeshSizeMin', 0.25)
    gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 0)
    gmsh.option.setNumber('Mesh.Binary', 1)
    for g in GROUPS:
        t0 = time.time()
        gmsh.option.setNumber('Mesh.MeshSizeMax', 5.0 if g == 'shell' else 3.0)
        gmsh.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assy.step'))
        solids = gmsh.model.getEntities(3)
        keep, drop = [], []
        for d, t in solids:
            b = gmsh.model.getBoundingBox(d, t)
            bb = (b[0], b[3], b[1], b[4], b[2], b[5])
            grp = classify(clean(gmsh.model.getEntityName(d, t)), bb)
            (keep if grp == g else drop).append((d, t))
        if drop:
            gmsh.model.occ.remove(drop, recursive=True)
        try:
            gmsh.model.mesh.generate(2)
        except Exception as e:
            print('  mesh failed (%s) -> fragment with slabs' % str(e)[:60], flush=True)
            kept_tags = [(d, t) for d, t in kept]
            bx = gmsh.model.occ.addBox(1.2, 900, 900, -0.6, -450, -450)
            bz = gmsh.model.occ.addBox(900, 900, 1.2, -450, -450, -0.6)
            objs, tools = gmsh.model.occ.fragment(kept_tags, [(3, bx), (3, bz)])
            gmsh.model.occ.remove(tools, recursive=True)
            gmsh.model.synchronize()
            gmsh.model.mesh.generate(2)
        ntri = 0
        for d, t in gmsh.model.getEntities(2):
            types, etags, nl = gmsh.model.mesh.getElements(2, t)
            for ti, tt in enumerate(types):
                ntri += len(etags[ti])
        path = os.path.join(OUT, g + '.stl')
        gmsh.write(path)
        sz = os.path.getsize(path) / 1e6
        print('%-6s keep=%3d drop=%3d tris=%7d  %5.2f MB  %.0fs'
              % (g, len(keep), len(drop), ntri, sz, time.time()-t0), flush=True)
        gmsh.finalize()
        gmsh.initialize()
        gmsh.option.setNumber('General.Terminal', 0)
        gmsh.option.setNumber('Mesh.MeshSizeMax', MESH_SIZE)
        gmsh.option.setNumber('Mesh.MeshSizeMin', 0.25)
        gmsh.option.setNumber('Mesh.MeshSizeFromCurvature', 0)
        gmsh.option.setNumber('Mesh.Binary', 1)
    gmsh.finalize()
    print('ALL DONE', flush=True)

run()
