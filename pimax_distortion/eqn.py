import math
from abc import ABC, abstractmethod
from typing import Optional, Tuple

import numpy as np

from pimax_distortion.params import HmdLensDistortionEqn, HmdLensDistortionParams, HmdParams

type Matrix = np.ndarray[Tuple[int, int], np.dtype[np.float64]]
type Vector = np.ndarray[Tuple[int], np.dtype[np.float64]]


class DistortionEqn(ABC):
    __slots__ = ('__weakref__',)

    @abstractmethod
    def evaluate(self, u: float, v: float) -> Tuple[float, float]:
        raise NotImplementedError()

    @abstractmethod
    def inverse_evaluate(self, u: float, v: float) -> Tuple[float, float]:
        raise NotImplementedError()


class DistortionEqnNone(DistortionEqn):
    __slots__ = ()

    def __init__(self):
        pass

    def evaluate(self, u: float, v: float) -> Tuple[float, float]:
        return 1.0, 1.0

    def inverse_evaluate(self, u: float, v: float) -> Tuple[float, float]:
        return 1.0, 1.0


class DistortionEqnPoly4(DistortionEqn):
    __slots__ = ('threshold', 'k')
    threshold: float
    k: Tuple[float, float, float, float]

    def __init__(self, threshold: float, k: Tuple[float, float, float, float]):
        threshold = float(threshold)
        k = tuple(float(x) for x in k)  # type: ignore
        if len(k) != 4:
            raise ValueError('must have exactly 4 coefficients')

        self.threshold = threshold
        self.k = k

    def evaluate(self, u: float, v: float) -> Tuple[float, float]:
        threshold = float(self.threshold)
        k = tuple(float(x) for x in self.k)

        distance_squared = u * u + v * v
        threshold_squared = threshold * threshold
        if distance_squared < threshold_squared:
            return k[0], k[0]

        t = distance_squared - threshold_squared

        res = type(self)._evaluate(k, t)  # type: ignore

        return res, res

    def inverse_evaluate(self, u: float, v: float) -> Tuple[float, float]:
        threshold = float(self.threshold)
        k = tuple(float(x) for x in self.k)

        distance = math.hypot(u, v)
        if distance < threshold:
            return k[0], k[0]

        best_guess = distance * 0.25
        threshold_squared = threshold * threshold

        guess_squared = best_guess * best_guess
        if guess_squared >= threshold_squared:
            t = guess_squared - threshold_squared
            res = type(self)._evaluate(k, t)  # type: ignore
        else:
            res = k[0]
        difference = abs(res * best_guess - distance)

        adjustment = best_guess
        for _ in range(16):
            lower_guess = best_guess - adjustment
            higher_guess = best_guess + adjustment

            guess_squared = lower_guess * lower_guess
            if guess_squared >= threshold_squared:
                t = guess_squared - threshold_squared
                res = type(self)._evaluate(k, t)  # type: ignore
            else:
                res = k[0]
            difference2 = abs(res * lower_guess - distance)

            guess_squared = higher_guess * higher_guess
            if guess_squared >= threshold_squared:
                t = guess_squared - threshold_squared
                res = type(self)._evaluate(k, t)  # type: ignore
            else:
                res = k[0]
            difference3 = abs(res * higher_guess - distance)

            if difference3 < difference:
                difference = difference3
                best_guess = higher_guess
            elif difference2 < difference:
                difference = difference2
                best_guess = lower_guess
            else:
                adjustment *= 0.5
                continue

            if difference <= 0.00001:
                break

        if distance == 0.0:
            return 1.0, 1.0
        res = best_guess / distance
        return res, res

    @staticmethod
    def _evaluate(k: Tuple[float, float, float, float], t: float) -> float:
        assert len(k) == 4
        return ((k[3] * t + k[2]) * t + k[1]) * t + k[0]


class DistortionEqnCatmullRom(DistortionEqn):
    __slots__ = ('max_radius', 'k', 'inv_max_radius', 'inv_k')
    max_radius: float
    k: Tuple[float, ...]
    inv_max_radius: Optional[float]
    inv_k: Optional[Tuple[float, ...]]

    def __init__(self, max_radius: float, k: Tuple[float, ...]):
        max_radius = float(max_radius)
        k = tuple(float(x) for x in k)
        n = len(k)
        if n < 4:
            raise ValueError('must have at least 4 coefficients')

        self.max_radius = max_radius
        self.k = k
        self.inv_max_radius = None
        self.inv_k = None

    def compute_inverse_params(self, terms: Optional[int] = None):
        max_radius = float(self.max_radius)
        k = tuple(float(x) for x in self.k)
        n = len(k)

        inv_n = int(terms) if terms is not None else n
        inv_max_radius = max_radius * type(self)._evaluate(k, n - 1)
        inv_k = [1.0]

        inv_max_radius_squared = inv_max_radius * inv_max_radius
        for i in range(1, inv_n):
            scaled_distance_squared = i * inv_max_radius_squared / (inv_n - 1)
            scaled_distance = math.sqrt(scaled_distance_squared)
            res = self._inverse_evaluate(scaled_distance) / scaled_distance
            inv_k.append(res)

        assert len(inv_k) == inv_n
        self.set_inverse_params(inv_max_radius, tuple(inv_k))

    def set_inverse_params(self, max_radius: float, k: Tuple[float, ...]):
        max_radius = float(max_radius)
        k = tuple(float(x) for x in k)
        n = len(k)
        if n < 4:
            raise ValueError('must have at least 4 coefficients')

        self.inv_max_radius = max_radius
        self.inv_k = k

    def evaluate(self, u: float, v: float) -> Tuple[float, float]:
        max_radius = float(self.max_radius)
        k = tuple(float(x) for x in self.k)
        n = len(k)

        distance_squared = u * u + v * v
        max_radius_squared = max_radius * max_radius
        scaled_distance_squared = \
            distance_squared * (n - 1) / max_radius_squared
        scale = type(self)._evaluate(k, scaled_distance_squared)
        return scale, scale

    def inverse_evaluate(self, u: float, v: float) -> Tuple[float, float]:
        inv_max_radius = self.inv_max_radius and float(self.inv_max_radius)
        inv_k = tuple(float(x) for x in (self.inv_k or ()))
        inv_n = len(self.inv_k or ())

        if inv_max_radius is not None:
            distance_squared = u * u + v * v
            inv_max_radius_squared = inv_max_radius * inv_max_radius
            scaled_distance_squared = \
                distance_squared * (inv_n - 1) / inv_max_radius_squared
            scale = type(self)._evaluate(inv_k, scaled_distance_squared)
            return scale, scale

        distance = math.hypot(u, v)
        if distance == 0.0:
            return 1.0, 1.0
        res = self._inverse_evaluate(distance)
        res /= distance
        return res, res

    def _inverse_evaluate(self, distance: float) -> float:
        max_radius = float(self.max_radius)
        k = tuple(float(x) for x in self.k)
        n = len(k)

        best_guess = distance * 0.25
        max_radius_squared = max_radius * max_radius

        distance_squared = best_guess * best_guess
        scaled_distance_squared = \
            distance_squared * (n - 1) / max_radius_squared
        scale = type(self)._evaluate(k, scaled_distance_squared)
        difference = abs(scale * best_guess - distance)

        adjustment = best_guess
        for _ in range(20):
            lower_guess = best_guess - adjustment
            higher_guess = best_guess + adjustment

            distance_squared = lower_guess * lower_guess
            scaled_distance_squared = \
                distance_squared * (n - 1) / max_radius_squared
            scale = type(self)._evaluate(k, scaled_distance_squared)
            difference2 = abs(scale * lower_guess - distance)

            distance_squared = higher_guess * higher_guess
            scaled_distance_squared = \
                distance_squared * (n - 1) / max_radius_squared
            scale = type(self)._evaluate(k, scaled_distance_squared)
            difference3 = abs(scale * higher_guess - distance)

            if difference3 < difference:
                difference = difference3
                best_guess = higher_guess
            elif difference2 < difference:
                difference = difference2
                best_guess = lower_guess
            else:
                adjustment *= 0.5
                continue

            if difference <= 0.00001:
                break

        return best_guess

    @staticmethod
    def _evaluate(k: Tuple[float, ...], scaled_value: float) -> float:
        n = len(k)
        assert n >= 4

        scaled_value_floor = int(math.floor(scaled_value))
        if scaled_value_floor <= 0:
            scaled_value_floor = 0
        elif scaled_value_floor >= n - 1:
            scaled_value_floor = n - 1

        t = scaled_value - scaled_value_floor
        i = scaled_value_floor

        if i == 0:
            p0 = k[0]
            m0 = k[1] - k[0]
            p1 = k[1]
            m1 = 0.5 * (k[2] - k[0])
        elif i == n - 2:
            p0 = k[n - 2]
            m0 = 0.5 * (k[n - 1] - k[n - 2])
            p1 = k[n - 1]
            m1 = k[n - 1] - k[n - 2]
        elif i == n - 1:
            p0 = k[n - 1]
            m0 = k[n - 1] - k[n - 2]
            p1 = p0 + m0
            m1 = m0
        else:
            p0 = k[i]
            m0 = 0.5 * (k[i + 1] - k[i - 1])
            p1 = k[i + 1]
            m1 = 0.5 * (k[i + 2] - k[i])

        omt = 1.0 - t

        res = (p0 * (1.0 + 2.0 * t) + m0 * t) * omt * omt + \
            (p1 * (1.0 + 2.0 * omt) - m1 * omt) * t * t

        return res


class DistortionEqnFixDegree(DistortionEqn):
    __slots__ = ('fix_radians', 'eye_relief', 'back_surface_to_display_distance',
                 'cos_angle', 'sin_angle', 'matrix_forward', 'matrix_backward',
                 'display_plane_normal', 'display_plane_point', 'inner')
    fix_radians: float
    eye_relief: float
    back_surface_to_display_distance: float
    cos_angle: float
    sin_angle: float
    matrix_forward: Matrix
    matrix_backward: Matrix
    display_plane_normal: Vector
    display_plane_point: Vector
    inner: DistortionEqn

    def __init__(self, fix_degree: float, eye_relief: float,
                 meters_per_tan_angle_at_center: float, inner: DistortionEqn):
        fix_degree = float(fix_degree)
        eye_relief = float(eye_relief)
        assert hasattr(inner, 'evaluate')

        fix_radians = math.radians(fix_degree)

        cos_angle = math.cos(fix_radians)
        sin_angle = math.sin(fix_radians)
        matrix_forward = np.array([
            [  cos_angle, 0.0, sin_angle, 0.0 ],
            [        0.0, 1.0,       0.0, 0.0 ],
            [ -sin_angle, 0.0, cos_angle, 0.0 ],
            [        0.0, 0.0,       0.0, 1.0 ],
        ], dtype=np.float64)

        cos_neg_angle = math.cos(-fix_radians)
        sin_neg_angle = math.sin(-fix_radians)
        matrix_backward = np.array([
            [  cos_neg_angle, 0.0, sin_neg_angle, 0.0 ],
            [            0.0, 1.0,           0.0, 0.0 ],
            [ -sin_neg_angle, 0.0, cos_neg_angle, 0.0 ],
            [            0.0, 0.0,           0.0, 1.0 ],
        ], dtype=np.float64)

        display_plane_normal = np.array([
            -sin_angle,
            0.0,
            -cos_angle,
        ], dtype=np.float64)
        display_plane_point = np.array([
            0.0,
            0.0,
            0.0,
        ], dtype=np.float64)

        self.fix_radians = fix_radians
        self.eye_relief = eye_relief
        self.back_surface_to_display_distance = meters_per_tan_angle_at_center
        self.cos_angle = cos_angle
        self.sin_angle = sin_angle
        self.matrix_forward = matrix_forward
        self.matrix_backward = matrix_backward
        self.display_plane_normal = display_plane_normal
        self.display_plane_point = display_plane_point
        self.inner = inner

    def evaluate(self, u: float, v: float) -> Tuple[float, float]:
        dtype = np.dtype(type(u + v))
        matrix_forward = self.matrix_forward.astype(dtype)

        uv_magnitude = math.hypot(u, v)

        uv01_vec = np.array([u, v, 0.0, 1.0], dtype=dtype)
        uv01_vec_transformed = np.matvec(matrix_forward, uv01_vec)
        uv_projected = uv01_vec_transformed[:2] / uv01_vec_transformed[3]
        #uv_projected[0] = -uv_projected[0]
        uv_projected_magnitude = np.linalg.norm(uv_projected)
        if uv_projected_magnitude != 0:
            uv_projected_direction = uv_projected / uv_projected_magnitude
        else:
            uv_projected_direction = np.zeros(2, dtype=dtype)

        current_magnitude = uv_magnitude

        new_uv = uv_projected_direction * current_magnitude
        res = self.inverse_evaluate(new_uv[0], new_uv[1])
        uv_magnitude2 = math.hypot(new_uv[0] * res[0], new_uv[1] * res[1])
        difference = abs(uv_magnitude2 - uv_magnitude)

        adjustment = uv_magnitude * 0.25
        for _ in range(20):
            lower_magnitude_guess = current_magnitude - adjustment
            higher_magnitude_guess = current_magnitude + adjustment

            new_uv = uv_projected_direction * lower_magnitude_guess
            res = self.inverse_evaluate(new_uv[0], new_uv[1])
            uv_magnitude2 = math.hypot(new_uv[0] * res[0], new_uv[1] * res[1])
            difference2 = abs(uv_magnitude2 - uv_magnitude)

            new_uv = uv_projected_direction * higher_magnitude_guess
            res = self.inverse_evaluate(new_uv[0], new_uv[1])
            uv_magnitude2 = math.hypot(new_uv[0] * res[0], new_uv[1] * res[1])
            difference3 = abs(uv_magnitude2 - uv_magnitude)

            if difference3 < difference:
                difference = difference3
                current_magnitude = higher_magnitude_guess
            elif difference2 < difference:
                difference = difference2
                current_magnitude = lower_magnitude_guess
            else:
                adjustment *= 0.5
                continue

            if difference <= 0.00001:
                break

        if u == 0.0:
            res_u = 1.0
        else:
            res_u = type(u)(uv_projected_direction[0] * current_magnitude / u)

        if v == 0.0:
            res_v = 1.0
        else:
            res_v = type(v)(uv_projected_direction[1] * current_magnitude / v)

        return res_u, res_v

    def inverse_evaluate(self, u: float, v: float) -> Tuple[float, float]:
        dtype = np.dtype(type(u + v))
        back_surface_to_display_distance = self.back_surface_to_display_distance
        display_plane_normal = self.display_plane_normal.astype(dtype)
        display_plane_point = self.display_plane_point.astype(dtype)
        matrix_backward = self.matrix_backward.astype(dtype)

        u1, v1 = self.inner.inverse_evaluate(u, v)
        u1s, v1s = u1 * u, v1 * v
        u2, v2 = self.scale(u, v)

        ray_origin_vec = np.array([
            u2,
            v2,
            -back_surface_to_display_distance,
        ], dtype=dtype)
        ray_direction_vec = np.array([
            back_surface_to_display_distance * u1s - u2,
            back_surface_to_display_distance * v1s - v2,
            back_surface_to_display_distance,
        ], dtype=dtype)

        num = np.dot(display_plane_point - ray_origin_vec, display_plane_normal)
        denom = np.dot(ray_direction_vec, display_plane_normal)
        t = num / denom
        hit_point_vec = ray_origin_vec + ray_direction_vec * t

        hit_point_vec_1 = np.array([*hit_point_vec, 1.0], dtype=dtype)
        unprojected_hit_point_vec = np.matvec(matrix_backward, hit_point_vec_1)

        z = unprojected_hit_point_vec[3]
        x = unprojected_hit_point_vec[0] / z
        y = unprojected_hit_point_vec[1] / z

        if u == 0.0:
            scale_u = 1.0
        else:
            scale_u = x / back_surface_to_display_distance / u

        if v == 0.0:
            scale_v = 1.0
        else:
            scale_v = y / back_surface_to_display_distance / v

        return scale_u, scale_v

    def scale(self, u: float, v: float) -> Tuple[float, float]:
        eye_relief = self.eye_relief
        return u * eye_relief, v * eye_relief


class DistortionEqnFixDegree2(DistortionEqnFixDegree):
    __slots__ = ('inner2',)
    inner2: DistortionEqn

    def __init__(self, fix_degree: float, eye_relief: float,
                 back_surface_to_display_distance: float, inner: DistortionEqn,
                 inner2: DistortionEqn):
        assert hasattr(inner2, 'evaluate')

        super().__init__(fix_degree=fix_degree, eye_relief=eye_relief,
                         meters_per_tan_angle_at_center=back_surface_to_display_distance,
                         inner=inner)
        self.inner2 = inner2

    def scale(self, u: float, v: float) -> Tuple[float, float]:
        inner2 = self.inner2

        u, v = super().scale(u, v)
        if inner2 is not None:
            su, sv = inner2.evaluate(u, v)
            u, v = u * su, v * sv

        return u, v


def _make_poly4_eqn(params: HmdLensDistortionParams) -> DistortionEqn:
    min_radius = params.MinRadius
    k = params.K
    assert len(k) == 4
    k = k[0], k[1], k[2], k[3]

    return DistortionEqnPoly4(
        threshold=min_radius,
        k=k
    )


def _make_catmull_rom_eqn(params: HmdLensDistortionParams) -> DistortionEqn:
    max_radius = params.MaxRadius
    k = tuple(params.K)

    eqn = DistortionEqnCatmullRom(
        max_radius=max_radius,
        k=k
    )
    eqn.compute_inverse_params()
    return eqn


def make_base_eqn(params: HmdLensDistortionParams) -> DistortionEqn:
    if params.eqn == HmdLensDistortionEqn.None_:
        return DistortionEqnNone()
    elif params.eqn == HmdLensDistortionEqn.Poly4:
        assert len(params.K) == 4
        return _make_poly4_eqn(params)
    elif params.eqn == HmdLensDistortionEqn.PointSamples:
        assert False and 'not implemented'
    elif params.eqn == HmdLensDistortionEqn.CatmullRom10:
        assert len(params.K) <= 11
        return _make_catmull_rom_eqn(params)
    elif params.eqn == HmdLensDistortionEqn.CatmullRom17:
        assert len(params.K) <= 18
        return _make_catmull_rom_eqn(params)
    elif params.eqn == HmdLensDistortionEqn.CatmullRom10Inv:
        assert False and 'not implemented'
    elif params.eqn == HmdLensDistortionEqn.CatmullRom17Inv:
        assert False and 'not implemented'
    else:
        assert False and 'invalid eqn value'


def make_eqn(params: HmdParams, eye: int) -> DistortionEqn:
    lens = params.lenses[0]
    eye_param = params.render.eyes[eye]
    distortion_param = lens.distortion_param
    back_surface_param = lens.back_surface_param
    meters_per_tan_angle_at_center = lens.MetersPerTanAngleAtCenter
    back_surface_to_display_distance = lens.BackSufaceToDisplayDistance
    eqn = distortion_param.eqn
    eye_relief = distortion_param.EyeRelief
    lens_fix_degree = eye_param.lens_fix_degree

    base_eqn = make_base_eqn(distortion_param)
    eqn = base_eqn
    if eqn != HmdLensDistortionEqn.None_ and lens_fix_degree != 0:
        assert eye_relief != 0

        if back_surface_param.eqn == HmdLensDistortionEqn.None_:
            eqn = DistortionEqnFixDegree(
                fix_degree=lens_fix_degree,
                eye_relief=eye_relief,
                meters_per_tan_angle_at_center=meters_per_tan_angle_at_center,
                inner=base_eqn
            )
        else:
            base_eqn2 = make_base_eqn(back_surface_param)
            eqn = DistortionEqnFixDegree2(
                fix_degree=lens_fix_degree,
                eye_relief=eye_relief,
                back_surface_to_display_distance=back_surface_to_display_distance,
                inner=base_eqn,
                inner2=base_eqn2,
            )

        if distortion_param.K_x_off_o or distortion_param.K_x_off_i:
            assert False and 'not implemented'
            #return DistortionEqnXOutterOff()

    return eqn
