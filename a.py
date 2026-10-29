import json
from itertools import batched

with open('/home/openglfreak/Downloads/mesh.json', 'r') as f:
    mesh_data = json.load(f)

for chunk in batched(mesh_data[0], 12):
    px, py, rx, ry, gx, gy, bx, by, *_ = chunk
    gx = gx * 0.6475935304603291 + 0.1282394692598004
    gy = gy * 0.8157509681884214 + 0.0
    gx = (gx + 1) / 2
    gy = (gy + 1) / 2
    print(gx, gy)
