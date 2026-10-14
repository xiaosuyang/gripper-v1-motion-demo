# -*- coding: utf-8 -*-
import gmsh, re, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'export_stl.py'), encoding='utf-8').read()
ns = {'__file__': os.path.join(HERE, 'export_stl.py')}
exec(src.split('def run()')[0], ns)
classify, clean = ns['classify'], ns['clean']

gmsh.initialize(); gmsh.option.setNumber('General.Terminal', 0)
gmsh.open(os.path.join(HERE, 'assy.step'))
out = []
for d, t in gmsh.model.getEntities(3):
    b = gmsh.model.getBoundingBox(d, t)
    bb = [b[0], b[3], b[1], b[4], b[2], b[5]]
    g = classify(clean(gmsh.model.getEntityName(d, t)), tuple(bb))
    if g:
        out.append({'bb': bb, 'g': g})
gmsh.finalize()
json.dump(out, open(os.path.join(HERE, 'groups.json'), 'w'), indent=0)
print('kept solids:', len(out))
import collections
print(collections.Counter(o['g'] for o in out))
