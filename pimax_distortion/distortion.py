import copy
import math
from typing import Tuple

from pimax_distortion.chroma import DistortionChroma, make_chroma
from pimax_distortion.ipd import adc_to_physical_separation, physical_separation_to_ipd
from pimax_distortion.params import HmdParams
from pimax_distortion.vars import DistortionVars
from pimax_distortion.rotate import rotate
from pimax_distortion.vectypes import NDCVec, UV01Vec


def _find_adc_value_from_separation(params: HmdParams, separation: float) -> Tuple[int, float]:
    best_adc = 0
    best_diff = math.inf
    for i in range(32768, 65536):
        _separation = adc_to_physical_separation(params, i, clamp=False)
        diff = abs(_separation - separation)
        if diff < best_diff:
            best_adc = i
            best_diff = diff
    return best_adc, best_diff


def _find_adc_value_from_ipd(params: HmdParams, ipd: float) -> Tuple[int, float, float]:
    best_adc = 0
    best_separation = 0.0
    best_diff = math.inf
    for i in range(32768, 65536):
        separation = adc_to_physical_separation(params, i, clamp=False)
        _ipd = physical_separation_to_ipd(params, separation, clamp=False)
        diff = abs(_ipd - ipd)
        if diff < best_diff:
            best_adc = i
            best_separation = separation
            best_diff = diff
    return best_adc, best_separation, best_diff


class LensDistortionOneEye:
    __slots__ = ('_eye', '_params', '_adc', '_separation', '_ipd', '_chroma',
                 '_vars', '__weakref__')
    _eye: int
    _params: HmdParams
    _adc: int
    _separation: float
    _ipd: float
    _chroma: DistortionChroma
    _vars: DistortionVars

    def __init__(self, eye: int, params: HmdParams):
        assert 0 <= eye <= 1
        assert isinstance(params, HmdParams)
        self._eye = int(eye)
        self._params = copy.copy(params)
        self._chroma = make_chroma(self.params, self.eye)
        self.separation = params.lenses[0].separation
        self._vars = self._make_vars()

    @property
    def eye(self) -> int:
        return self._eye

    @property
    def params(self) -> HmdParams:
        return copy.copy(self._params)

    @property
    def adc(self) -> int:
        return self._adc

    @adc.setter
    def adc(self, value: int):
        separation = adc_to_physical_separation(self.params, value)
        ipd = physical_separation_to_ipd(self.params, separation)
        self._adc = value
        self._separation = separation
        self._ipd = ipd
        self._vars = self._make_vars()

    @property
    def separation(self) -> float:
        return self._separation

    @separation.setter
    def separation(self, value: float):
        assert value >= 0
        value += 0.0
        adc, diff = _find_adc_value_from_separation(self.params, value)
        assert diff < 0.001
        ipd = physical_separation_to_ipd(self.params, value)
        self._adc = adc
        self._separation = value
        self._ipd = ipd
        self._vars = self._make_vars()

    @property
    def ipd(self) -> float:
        return self._ipd

    @ipd.setter
    def ipd(self, value: float):
        assert value >= 0
        value += 0.0
        adc, separation, diff = _find_adc_value_from_ipd(self.params, value)
        assert diff < 0.001
        self._adc = adc
        self._separation = separation
        self._ipd = value
        self._vars = self._make_vars()

    def _make_vars(self) -> DistortionVars:
         eqn = self._chroma.inner
         params = copy.copy(self.params)
         params.lenses[0].separation = self.separation
         return DistortionVars.from_params_eqn(params=params, eqn=eqn)

    def calculate(self, u: float, v: float, use_numpy: bool = False) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        eye = self.eye
        params = self.params
        vars = self._vars
        chroma = self._chroma
        eye_params = params.render.eyes[eye]
        eye_rotation = eye_params.rotate
        scaling = vars.scaling.eyes[eye]
        factors = vars.factors[eye]
        lens_center_uv = scaling.lens_center
        tan_eye_angle_scale_uv = scaling.scale
        eye_to_source_scale_uv = factors.eye_to_source_scale_uv
        eye_to_source_offset_uv = factors.eye_to_source_offset_uv

        _u, _v = u, v
        if use_numpy:
            import numpy as np
            _u, _v = np.float32(u), np.float32(v)

        uv = UV01Vec(_u, _v)
        ndc = uv.to_ndc()

        display_rotation = eye_rotation.inverse()
        rotated = NDCVec(*rotate(ndc.u_ndc, ndc.v_ndc, display_rotation))
        scaled = NDCVec(
            type(rotated.u_ndc)((rotated.u_ndc - lens_center_uv.u_ndc) * tan_eye_angle_scale_uv.u_tan),
            type(rotated.v_ndc)((rotated.v_ndc - lens_center_uv.v_ndc) * tan_eye_angle_scale_uv.v_tan),
        )

        res_r, res_g, res_b = chroma.evaluate_rgb(scaled.u_ndc, scaled.v_ndc)  # type: ignore
        res_r = NDCVec(res_r[0] * scaled.u_ndc, res_r[1] * scaled.v_ndc)
        res_g = NDCVec(res_g[0] * scaled.u_ndc, res_g[1] * scaled.v_ndc)
        res_b = NDCVec(res_b[0] * scaled.u_ndc, res_b[1] * scaled.v_ndc)

        res_r = NDCVec(
            (res_r.u_ndc * eye_to_source_scale_uv.u_tan) + eye_to_source_offset_uv.u_ndc,
            (res_r.v_ndc * eye_to_source_scale_uv.v_tan) + eye_to_source_offset_uv.v_ndc,
        )
        res_g = NDCVec(
            (res_g.u_ndc * eye_to_source_scale_uv.u_tan) + eye_to_source_offset_uv.u_ndc,
            (res_g.v_ndc * eye_to_source_scale_uv.v_tan) + eye_to_source_offset_uv.v_ndc,
        )
        res_b = NDCVec(
            (res_b.u_ndc * eye_to_source_scale_uv.u_tan) + eye_to_source_offset_uv.u_ndc,
            (res_b.v_ndc * eye_to_source_scale_uv.v_tan) + eye_to_source_offset_uv.v_ndc,
        )

        res_r = res_r.to_01()
        res_g = res_g.to_01()
        res_b = res_b.to_01()

        return (
            (float(res_r.u_01), float(res_r.v_01)),
            (float(res_g.u_01), float(res_g.v_01)),
            (float(res_b.u_01), float(res_b.v_01)),
        )
