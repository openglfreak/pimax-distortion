import json
import math
from typing import Tuple

from pimax_distortion.chroma import DistortionChroma
from pimax_distortion.distortion import LensDistortionOneEye
from pimax_distortion.eqn import DistortionEqnCatmullRom, DistortionEqnFixDegree
from pimax_distortion.ipd import adc_to_physical_separation
from pimax_distortion.ndc import from_ndc_uv, to_ndc_uv
from pimax_distortion.params import HmdParams
from pimax_distortion.vars import DistortionVars
from pimax_distortion.rotate import rotate

__eye = 0
#__adc = 33641  #pi_server.DMP
#__adc = 36760  # 0.06
#__adc = 33695  # 0.07
__adc = 36446  # meshDump.json


path = '/home/openglfreak/Pimax/JSONs/Pimax P2 5K Formal B.json'
#path = '/home/openglfreak/Pimax/JSONs/Pimax P2 8K Formal EA.json'
#path = '/home/openglfreak/Pimax/JSONs/Pimax P2 5K Formal Y.json'
with open(path, 'r') as f:
    config = json.load(f)

params = HmdParams.from_dict(config)
params.lenses[0].separation = adc_to_physical_separation(params, __adc)

inner = DistortionEqnCatmullRom(
    max_radius=params.lenses[0].distortion_param.MaxRadius,
    k=tuple(params.lenses[0].distortion_param.K)
)

outer = DistortionEqnFixDegree(
    fix_degree=params.render.eyes[__eye].lens_fix_degree,
    eye_relief=params.lenses[0].distortion_param.EyeRelief,
    meters_per_tan_angle_at_center=params.lenses[0].MetersPerTanAngleAtCenter,
    inner=inner
)

chroma = DistortionChroma(
    k=tuple(params.lenses[0].distortion_param.ChromaticAberration),
    inner=outer
)
post_vars = DistortionVars.from_params_eqn(params, outer)

inner.compute_inverse_params()

if False:
    with open('/home/openglfreak/.config/pimax/meshes/p2b.json', 'r') as f:
        data = json.load(f)
    first_res = data[0]
    first_mesh = list(first_res['meshes'].values())[0][__eye]
    points = first_mesh['points']
    record_stride = 4 * 2
else:
    with open('/home/openglfreak/Downloads/meshDump.json', 'r') as f:
        data = json.load(f)
    first_ipd = list(data.values())[0]
    first_eye = first_ipd[0]
    points = first_eye['points']
    record_stride = 6 * 2

row_stride = 65 * record_stride
def get_record(x, y):
    i = y * row_stride + x * record_stride
    return points[i:i+record_stride]

'''
def _find_adc_value_from_ipd(ipd: float) -> Tuple[int, float]:
    min_adc = 32768
    separation = adc_to_physical_separation(params, min_adc, clamp=False)
    _ipd = physical_separation_to_ipd(params, separation, clamp=False)
    min_diff = abs(_ipd - ipd)
    for i in range(min_adc + 1, 65536):
        separation = adc_to_physical_separation(params, i, clamp=False)
        _ipd = physical_separation_to_ipd(params, separation, clamp=False)
        diff = abs(_ipd - ipd)
        if diff < min_diff:
            min_adc = i
            min_diff = diff
    return min_adc, min_diff


def _find_adc_value_from_ipd(ipd: float) -> Tuple[int, float]:
    min_adc = 0
    min_diff = math.inf
    for i in range(min_adc + 1, 65536):
        separation = adc_to_physical_separation(params, i, clamp=False)
        _ipd = physical_separation_to_ipd(params, separation, clamp=False)
        diff = abs(_ipd - ipd)
        if diff < min_diff:
            min_adc = i
            min_diff = diff
    return min_adc, min_diff
'''


def _apply_eqn(
    ndc_u: float,
    ndc_v: float,
    eqn: DistortionChroma,
) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    res_r, res_g, res_b = eqn.evaluate_rgb(ndc_u, ndc_v)
    res_r = (res_r[0] * ndc_u, res_r[1] * ndc_v)
    res_g = (res_g[0] * ndc_u, res_g[1] * ndc_v)
    res_b = (res_b[0] * ndc_u, res_b[1] * ndc_v)
    return res_r, res_g, res_b


def _apply_fov_fix(
    u: float,
    v: float,
    fov_fix_degree: float,
) -> Tuple[float, float]:
    fov_fix_radians = math.radians(fov_fix_degree)

    au = math.atan(u)
    cau = math.cos(abs(au))

    theta = au - fov_fix_radians
    if theta > math.radians(89):
        theta = math.radians(89)
    if theta <= math.radians(-89):
        theta = math.radians(-89)

    res_u = math.tan(theta)
    ct = math.cos(abs(theta))
    res_v = math.copysign(abs((cau / ct) * v), v)

    return res_u, res_v


def _calculate_inner(
    eye: int,
    ndc_u: float,
    ndc_v: float,
    eqn: DistortionChroma,
    fov_fix: bool,
) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    scaling = post_vars.scaling.eyes[eye]
    factors = post_vars.factors[eye]
    lens_center_uv = scaling.lens_center
    tan_eye_angle_scale_uv = scaling.scale
    fov_fix_degree = params.render.eyes[eye].fov_fix_degree
    if fov_fix:
        eye_to_source_scale_uv = factors.eye_to_source_scale_with_fov_fix_uv
        eye_to_source_offset_uv = factors.eye_to_source_offset_with_fov_fix_uv
    else:
        eye_to_source_scale_uv = factors.eye_to_source_scale_uv
        eye_to_source_offset_uv = factors.eye_to_source_offset_uv

    inp_scaled_u = type(ndc_u)((ndc_u - lens_center_uv.u_ndc) * tan_eye_angle_scale_uv.u_tan)
    inp_scaled_v = type(ndc_v)((ndc_v - lens_center_uv.v_ndc) * tan_eye_angle_scale_uv.v_tan)

    res_r, res_g, res_b = _apply_eqn(inp_scaled_u, inp_scaled_v, eqn)

    if fov_fix and fov_fix_degree != 0:
        res_r = _apply_fov_fix(res_r[0], res_r[1], fov_fix_degree)
        res_g = _apply_fov_fix(res_g[0], res_g[1], fov_fix_degree)
        res_b = _apply_fov_fix(res_b[0], res_b[1], fov_fix_degree)

    res_r = (
        type(res_r[0])((res_r[0] * eye_to_source_scale_uv.u_tan) + eye_to_source_offset_uv.u_ndc),
        type(res_r[1])((res_r[1] * eye_to_source_scale_uv.v_tan) + eye_to_source_offset_uv.v_ndc),
    )
    res_g = (
        type(res_g[0])((res_g[0] * eye_to_source_scale_uv.u_tan) + eye_to_source_offset_uv.u_ndc),
        type(res_g[1])((res_g[1] * eye_to_source_scale_uv.v_tan) + eye_to_source_offset_uv.v_ndc),
    )
    res_b = (
        type(res_b[0])((res_b[0] * eye_to_source_scale_uv.u_tan) + eye_to_source_offset_uv.u_ndc),
        type(res_b[1])((res_b[1] * eye_to_source_scale_uv.v_tan) + eye_to_source_offset_uv.v_ndc),
    )

    #if eye == 1:
    #    res_r = (-res_r[0], res_r[1])
    #    res_g = (-res_g[0], res_g[1])
    #    res_b = (-res_b[0], res_b[1])

    res_r = from_ndc_uv(res_r[0], res_r[1])
    res_g = from_ndc_uv(res_g[0], res_g[1])
    res_b = from_ndc_uv(res_b[0], res_b[1])

    return res_r, res_g, res_b


def _calculate(
    eye: int,
    u: float,
    v: float,
    eqn: DistortionChroma,
) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
    ndc_u, ndc_v = to_ndc_uv(u, v)

    eye_rotation = params.render.eyes[eye].rotate.inverse()
    rot_u, rot_v = rotate(ndc_u, ndc_v, eye_rotation)

    res_r, res_g, res_b = _calculate_inner(eye, rot_u, rot_v, eqn, False)

    return res_r, res_g, res_b


matrices = [[0, 1, -1, 0], [0, -1, 1, 0]]
inv_matrices = [[0, -1, 1, 0], [0, 1, -1, 0]]


def rotmat(vec : tuple, mat : list) -> tuple:
    vec = (vec[0]*2 - 1, vec[1]*2 - 1)
    ovec = (mat[0] * vec[0] + mat[1] * vec[1], mat[2] * vec[0] + mat[3] * vec[1])
    return ((ovec[0]+1)/2, (ovec[1]+1)/2)



'''
px, py = 0.0, 0.5
_px, _py = rotmat((px, py), matrices[__eye])
#_px, _py = np.float32(0.4), np.float32(0.4)
print(_px, _py)
res_r, res_g, res_b = _calculate(__eye, _px, _py, chroma)  # type: ignore
print(*res_g)
raise SystemExit(1)
'''

new_data = {}
new_data['fov'] = [
    -math.atan(post_vars.factors[__eye].bounds.up_tan),
    math.atan(post_vars.factors[__eye].bounds.down_tan),
    math.atan(post_vars.factors[__eye].bounds.left_tan),
    -math.atan(post_vars.factors[__eye].bounds.right_tan),
]

new_points = []

lens_distortion = LensDistortionOneEye(0, params)

file0 = open('/tmp/w.txt', 'w')
file1 = open('/tmp/a.txt', 'w')
file2 = open('/tmp/b.txt', 'w')
file3 = open('/tmp/c.txt', 'w')
step = 1
for y in range(0, 65, step): # (0, 1, 10, 24, 32, 64): #
    for x in range(0, 65, step):
        px, py, rx, ry, gx, gy, bx, by = get_record(x, y)[:8]

        _px, _py = rotmat((px, py), matrices[__eye])
        #_px, _py = np.float32(_px), np.float32(_py)
        #_px, _py = np.longdouble(_px), np.longdouble(_py)
        res_r, res_g, res_b = lens_distortion.calculate(_px, _py, use_numpy=True)  # type: ignore

        print('{:.18f}'.format(float(gx)), '{:.18f}'.format(float(gy)), file=file0)
        #print('{:.18f}'.format(float(res_r[0])), '{:.18f}'.format(float(res_r[1])), file=file1)
        print('{:.18f}'.format(float(res_g[0])), '{:.18f}'.format(float(res_g[1])), file=file2)
        #print('{:.18f}'.format(float(res_b[0])), '{:.18f}'.format(float(res_b[1])), file=file3)

        #new_points.extend([float(px), float(py)])
        #new_points.extend([float(res_r[0]), float(res_r[1])])
        #new_points.extend([float(res_g[0]), float(res_g[1])])
        #new_points.extend([float(res_b[0]), float(res_b[1])])
file3.close()
file2.close()
file1.close()
file0.close()

#new_data['points'] = new_points

#with open('/tmp/eye-' + str(__adc) + '-' + str(__eye) + '.json', 'w') as f:
#    json.dump(new_data, f)
