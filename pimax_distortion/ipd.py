import math

from pimax_distortion.params import HmdParams


def adc_to_physical_separation(params: HmdParams, raw: int, clamp: bool = True) -> float:
    assert raw >= -32768
    assert raw <= 65535

    adc_to_separation_K = params.lenses[0].adc_to_separation_K

    if raw < 0 or (raw & 0x8000) != 0:
        a = (raw & 0x7fff) * adc_to_separation_K[1] + adc_to_separation_K[0]
    else:
        a = float(raw)

    b = a / 50
    c = min(max(b, 80), 120) if clamp else b
    d = c / 1000

    return d


def physical_separation_to_ipd(params: HmdParams, separation: float, offset: float = 0.0, clamp: bool = True) -> float:
    assert params.render.lens_separation_to_ipd_rate != 0

    lens_separation_to_ipd_rate = params.render.lens_separation_to_ipd_rate
    fov_fix_degree = params.render.eyes[0].fov_fix_degree
    lens_fix_degree = params.render.eyes[0].lens_fix_degree

    fov_fix_radians = math.radians(fov_fix_degree)
    lens_fix_radians = math.radians(lens_fix_degree)

    theta = fov_fix_radians - lens_fix_radians
    ipd = math.cos(theta) * separation - math.sin(fov_fix_radians) * (2 * lens_separation_to_ipd_rate)
    ipd_clamped = min(max(ipd, 0.06), 0.07) if clamp else ipd
    ipd_clamped_with_offset = ipd_clamped + math.cos(theta) * offset

    return ipd_clamped_with_offset
