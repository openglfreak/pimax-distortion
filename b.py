import json

with open('/tmp/eye-36760-0.json', 'r') as f:
    mesh_006_l = json.load(f)
with open('/tmp/eye-36760-1.json', 'r') as f:
    mesh_006_r = json.load(f)
with open('/tmp/eye-33695-0.json', 'r') as f:
    mesh_007_l = json.load(f)
with open('/tmp/eye-33695-1.json', 'r') as f:
    mesh_007_r = json.load(f)

mesh_006 = [mesh_006_l, mesh_006_r]
mesh_007 = [mesh_007_l, mesh_007_r]

data = {
    'resolutions': [
      {
        'width': 2560,
        'height': 1440
      }
    ],
    'refresh_rates': [
      82,
      72,
      64
    ],
    'meshes': {
      '0.06': mesh_006,
      '0.07': mesh_007,
    },
}

with open('/tmp/p2b.json', 'w') as f:
    json.dump([data], f)
