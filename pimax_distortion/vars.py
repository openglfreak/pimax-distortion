import math
from copy import copy
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from pimax_distortion.eqn import DistortionEqn
from pimax_distortion.math import apply_extra_fov, tangent_add
from pimax_distortion.params import HmdParams, HmdRenderEyeRotation, HmdRenderEyeViewPort
from pimax_distortion.recttypes import TanAnglesRect
from pimax_distortion.vectypes import MetersVec, NDCVec, TanAnglesVec


@dataclass
class DisplayDimensions:
    display_size: MetersVec
    eye_sizes: Tuple[MetersVec, MetersVec]

    @staticmethod
    def calculate_eye_size(params: HmdParams, eye: int) -> MetersVec:
        display = params.displays[eye % len(params.displays)]
        eye_param = params.render.eyes[eye]
        h_size = display.h_size
        v_size = display.v_size
        view_port = eye_param.view_port

        size_u = 0.0
        size_v = 0.0

        if view_port == HmdRenderEyeViewPort.full:
            size_u = h_size
            size_v = v_size
        elif view_port in (HmdRenderEyeViewPort.top, HmdRenderEyeViewPort.bottom):
            size_u = h_size
            size_v = v_size / 2
        elif view_port in (HmdRenderEyeViewPort.left, HmdRenderEyeViewPort.right):
            size_u = h_size / 2
            size_v = v_size
        else:
            assert False and 'invalid view_port'

        if eye_param.rotate in (HmdRenderEyeRotation.R_90, HmdRenderEyeRotation.R_270):
            size_u, size_v = size_v, size_u

        return MetersVec(size_u, size_v)

    @staticmethod
    def from_params(params: HmdParams) -> DisplayDimensions:
        eye_size_l = __class__.calculate_eye_size(params, 0)
        eye_size_r = __class__.calculate_eye_size(params, 1)
        eye_sizes = (eye_size_l, eye_size_r)

        display_width_meters = eye_size_l.u_m + eye_size_r.u_m
        display_height_meters = max(0.0, eye_size_l.v_m, eye_size_r.v_m)
        display_size = MetersVec(display_width_meters, display_height_meters)

        return DisplayDimensions(
            display_size=display_size,
            eye_sizes=eye_sizes,
        )


@dataclass
class DisplayScalingOneEye:
    lens_center: NDCVec
    scale: TanAnglesVec

    @staticmethod
    def from_params(
        params: HmdParams,
        dimensions: DisplayDimensions,
        eye: int,
    ) -> DisplayScalingOneEye:
        display = params.displays[eye % len(params.displays)]
        lens = params.lenses[eye % len(params.lenses)]
        gap = display.gap[eye]
        separation = lens.separation
        v_center_off = lens.v_center_off[eye]
        meters_per_tan_angle_at_center = lens.MetersPerTanAngleAtCenter
        eye_sizes = dimensions.eye_sizes

        display_width_meters = eye_sizes[0].u_m + eye_sizes[1].u_m
        display_height_meters = max(0.0, eye_sizes[0].v_m, eye_sizes[1].v_m)

        scale = TanAnglesVec(
            0.25 * display_width_meters / meters_per_tan_angle_at_center,
            0.5 * display_height_meters / meters_per_tan_angle_at_center,
        )

        _lens_center_u = (display_width_meters + gap - separation) / 2
        _lens_center_v = display_height_meters / 2 + v_center_off
        if eye == 1:
            _lens_center_u = -_lens_center_u
        lens_center = NDCVec(
            (_lens_center_u / (display_width_meters / 2)) * 2 - 1,
            (_lens_center_v / display_height_meters) * 2 - 1,
        )

        return DisplayScalingOneEye(
            lens_center=lens_center,
            scale=scale,
        )


@dataclass
class DisplayScaling:
    eyes: Tuple[DisplayScalingOneEye, DisplayScalingOneEye]

    @staticmethod
    def from_params(
        params: HmdParams,
        dimensions: DisplayDimensions,
    ) -> DisplayScaling:
        eyes = (
            DisplayScalingOneEye.from_params(params, dimensions, 0),
            DisplayScalingOneEye.from_params(params, dimensions, 1),
        )
        return DisplayScaling(eyes=eyes)


@dataclass
class RenderDiameter:
    render_diameter: float = 0.0
    periphery_render_diameter: float = 0.0

    @staticmethod
    def from_params(eye: int, params: HmdParams) -> RenderDiameter:
        lens = params.lenses[min(eye, len(params.lenses) - 1)]
        periphery_render_type = lens.periphery_render_type
        periphery_diameter = lens.periphery_diameter

        render_diameter = lens.diameter
        periphery_render_diameter = 0
        if periphery_render_type == 1:
            render_diameter = periphery_diameter
        elif periphery_render_type == 2:
            periphery_render_diameter = periphery_diameter

        return RenderDiameter(
            render_diameter=render_diameter,
            periphery_render_diameter=periphery_render_diameter,
        )


@dataclass
class LensFov:
    main_fov: TanAnglesRect
    periphery_fov: TanAnglesRect
    periphery_fov_with_fix: TanAnglesRect

    @staticmethod
    def _calculate_fov(
        lens_diameter: float,
        eye_relief: float,
        h_offset: float,
        v_offset: float,
        rot_rad: float,
    ) -> TanAnglesRect:
        pupil_radius = 0.0135
        pull = 0.001

        deg_30_radians = math.radians(30.0)
        rot_rad = min(max(rot_rad, 0.0), deg_30_radians)

        half_lens = lens_diameter / 2

        up = (half_lens + v_offset) / eye_relief
        down = (half_lens - v_offset) / eye_relief
        left = (half_lens + h_offset) / eye_relief
        right = (half_lens - h_offset) / eye_relief

        if rot_rad > 0.0:
            s, c = math.sin(rot_rad), math.cos(rot_rad)

            sideways = pupil_radius * s + pull * (rot_rad / deg_30_radians)
            rolled_eye_relief = eye_relief + pupil_radius * (1.0 - c)

            rolled_up = (half_lens + v_offset + sideways) / rolled_eye_relief
            rolled_down = (half_lens - v_offset + sideways) / rolled_eye_relief
            rolled_left = (half_lens + h_offset + sideways) / rolled_eye_relief
            rolled_right = (half_lens - h_offset + sideways) / rolled_eye_relief

            if up < rolled_up:
                up = rolled_up
            if down < rolled_down:
                down = rolled_down
            if left < rolled_left:
                left = rolled_left
            if right < rolled_right:
                right = rolled_right

        return TanAnglesRect(up, down, left, right)

    @staticmethod
    def _calculate_distortion(
        scaling: DisplayScalingOneEye,
        eqn: DistortionEqn,
        u: float,
        v: float,
    ) -> Tuple[float, float]:
        tan_u = (u - scaling.lens_center.u_ndc) * scaling.scale.u_tan
        tan_v = (v - scaling.lens_center.v_ndc) * scaling.scale.v_tan
        scale_u, scale_v = eqn.evaluate(tan_u, tan_v)  # type: ignore
        distorted_u, distorted_v = tan_u * scale_u, tan_v * scale_v
        return type(u)(distorted_u), type(v)(distorted_v)

    @staticmethod
    def _calculate_distortion_fov(
        scaling: DisplayScalingOneEye,
        eqn: DistortionEqn,
        lens_center_u: float,
        lens_center_v: float,
        edge_u: float,
        edge_v: float,
        steps: int,
    ) -> TanAnglesRect:
        assert steps >= 2

        res = TanAnglesRect()

        for i in range(0, steps):
            f = i / (steps - 1)
            x = lens_center_u + (edge_u - lens_center_u) * f
            y = lens_center_v + (edge_v - lens_center_v) * f
            dx, dy = __class__._calculate_distortion(
                scaling,
                eqn,
                x,
                y
            )

            if res.up_tan < -dy:
                res.up_tan = -dy
            if res.down_tan < dy:
                res.down_tan = dy
            if res.left_tan < -dx:
                res.left_tan = -dx
            if res.right_tan < dx:
                res.right_tan = dx

        return res

    @staticmethod
    def calculate_fov(
        eye: int,
        scaling: DisplayScalingOneEye,
        eqn: DistortionEqn,
        lens_diameter: float,
        lens_inner_diameter: float,
        eye_relief: float,
        rot_rad: float,
    ) -> TanAnglesRect:
        lens_center_x = np.float32(scaling.lens_center.u_ndc)
        lens_center_y = np.float32(scaling.lens_center.v_ndc)

        res = __class__._calculate_fov(
            np.float32(lens_diameter),  # type: ignore
            np.float32(max(0.006, eye_relief)),  # type: ignore
            np.float32(0.0),  # type: ignore
            np.float32(0.0),  # type: ignore
            np.float32(rot_rad),  # type: ignore
        )

        if lens_inner_diameter != 0.0:
            res2 = __class__._calculate_fov(
                np.float32(lens_inner_diameter),  # type: ignore
                np.float32(max(0.006, eye_relief)),  # type: ignore
                np.float32(0.0),  # type: ignore
                np.float32(0.0),  # type: ignore
                np.float32(rot_rad),  # type: ignore
            )

            if eye == 0:
                if res2.right_tan < res.right_tan:
                    res.right_tan = res2.right_tan
            else:
                if res2.left_tan < res.left_tan:
                    res.left_tan = res2.left_tan

        left = __class__._calculate_distortion_fov(
            scaling,
            eqn,
            lens_center_x,  # type: ignore
            lens_center_y,  # type: ignore
            -1.0,
            lens_center_y,  # type: ignore
            10,
        )
        right = __class__._calculate_distortion_fov(
            scaling,
            eqn,
            lens_center_x,  # type: ignore
            lens_center_y,  # type: ignore
            1.0,
            lens_center_y,  # type: ignore
            10,
        )
        up = __class__._calculate_distortion_fov(
            scaling,
            eqn,
            lens_center_x,  # type: ignore
            lens_center_y,  # type: ignore
            lens_center_x,  # type: ignore
            -1.0,
            10,
        )
        down = __class__._calculate_distortion_fov(
            scaling,
            eqn,
            lens_center_x,  # type: ignore
            lens_center_y,  # type: ignore
            lens_center_x,  # type: ignore
            1.0,
            10,
        )

        if res.up_tan > up.up_tan:
            res.up_tan = up.up_tan
        if res.down_tan > down.down_tan:
            res.down_tan = down.down_tan
        if res.left_tan > left.left_tan:
            res.left_tan = left.left_tan
        if res.right_tan > right.right_tan:
            res.right_tan = right.right_tan

        return res

    @staticmethod
    def from_params_scaling_eqn_diam(eye: int, params: HmdParams,
                                     scaling: DisplayScalingOneEye, eqn: DistortionEqn,
                                     diam: RenderDiameter) -> LensFov:
        lens = params.lenses[min(eye, len(params.lenses) - 1)]
        lens_diameter = lens.diameter
        lens_inner_diameter = lens.inner_diameter
        periphery_diameter = lens.periphery_diameter
        eye_relief = params.default_eye_relief
        extra = params.render.fov.extra
        extra_fix = params.render.fov.extra_fix
        lens_fix_degree = params.render.eyes[eye].lens_fix_degree
        fov_fix_degree = params.render.eyes[eye].fov_fix_degree
        periphery_render_diameter = diam.periphery_render_diameter

        main_fov = __class__.calculate_fov(
            eye,
            scaling,
            eqn,
            lens_diameter,
            lens_inner_diameter,
            eye_relief,
            lens_fix_degree,
        )

        if periphery_render_diameter <= 0:
            if periphery_diameter > 0:
                _periphery_fov = __class__.calculate_fov(
                    eye,
                    scaling,
                    eqn,
                    periphery_diameter,
                    0.0,
                    eye_relief,
                    lens_fix_degree,
                )

                if eye == 0:
                    main_fov.left_tan = _periphery_fov.left_tan
                else:
                    main_fov.right_tan = _periphery_fov.right_tan
                if main_fov.up_tan < _periphery_fov.up_tan:
                    main_fov.up_tan = _periphery_fov.up_tan
                if main_fov.down_tan < _periphery_fov.down_tan:
                    main_fov.down_tan = _periphery_fov.down_tan

            periphery_fov = copy(main_fov)
        else:
            periphery_fov = __class__.calculate_fov(
                eye,
                scaling,
                eqn,
                periphery_render_diameter,
                0.0,
                eye_relief,
                lens_fix_degree,
            )

            if periphery_fov.left_tan < main_fov.left_tan:
                periphery_fov.left_tan = main_fov.left_tan
            if periphery_fov.right_tan < main_fov.right_tan:
                periphery_fov.right_tan = main_fov.right_tan
            if periphery_fov.up_tan < main_fov.up_tan:
                periphery_fov.up_tan = main_fov.up_tan
            if periphery_fov.down_tan < main_fov.down_tan:
                periphery_fov.down_tan = main_fov.down_tan

        periphery_fov = apply_extra_fov(
            eye,
            periphery_fov,
            extra,
        )

        periphery_fov_with_fix = periphery_fov
        if fov_fix_degree != 0:
            fov_fix_radians = math.radians(fov_fix_degree)
            fov_fix_tan = math.tan(fov_fix_radians)

            if eye == 0:
                periphery_fov.left_tan = tangent_add(
                    periphery_fov.left_tan,
                    -fov_fix_tan,
                )
                if main_fov.left_tan > periphery_fov.left_tan:
                    main_fov.left_tan = periphery_fov.left_tan
            else:
                periphery_fov.right_tan = tangent_add(
                    periphery_fov.right_tan,
                    -fov_fix_tan,
                )
                if main_fov.right_tan > periphery_fov.right_tan:
                    main_fov.right_tan = periphery_fov.right_tan

            periphery_fov_with_fix = TanAnglesRect(
                periphery_fov.up_tan,
                periphery_fov.down_tan,
                tangent_add(periphery_fov.left_tan, fov_fix_tan),
                tangent_add(periphery_fov.right_tan, -fov_fix_tan),
            )

            periphery_fov_with_fix = apply_extra_fov(
                eye,
                periphery_fov_with_fix,
                extra_fix,
            )

        return LensFov(
            main_fov=main_fov,
            periphery_fov=periphery_fov,
            periphery_fov_with_fix=periphery_fov_with_fix,
        )


@dataclass
class EyeToSourceFactors:
    bounds: TanAnglesRect
    eye_to_source_scale_uv: TanAnglesVec
    eye_to_source_offset_uv: NDCVec

    bounds_with_fov_fix: TanAnglesRect
    eye_to_source_scale_with_fov_fix_uv: TanAnglesVec
    eye_to_source_offset_with_fov_fix_uv: NDCVec

    bounds_min_vert: TanAnglesRect
    bounds_with_fov_fix_min_vert: TanAnglesRect
    clamped_bounds_min_vert: TanAnglesRect

    @staticmethod
    def from_params_scaling_eqn(params: HmdParams, scaling: DisplayScalingOneEye,
                                eye: int, eqn: DistortionEqn) -> EyeToSourceFactors:
        render_diam = RenderDiameter.from_params(eye, params)
        lens_fov = LensFov.from_params_scaling_eqn_diam(
            eye,
            params,
            scaling,
            eqn,
            render_diam
        )

        eye_to_source_scale = TanAnglesVec(
            2.0 / (lens_fov.periphery_fov.left_tan + lens_fov.periphery_fov.right_tan),
            2.0 / (lens_fov.periphery_fov.up_tan + lens_fov.periphery_fov.down_tan),
        )
        eye_to_source_offset = NDCVec(
            (lens_fov.periphery_fov.left_tan - lens_fov.periphery_fov.right_tan) /
                (lens_fov.periphery_fov.left_tan + lens_fov.periphery_fov.right_tan),
            (lens_fov.periphery_fov.up_tan - lens_fov.periphery_fov.down_tan) /
                (lens_fov.periphery_fov.up_tan + lens_fov.periphery_fov.down_tan),
        )

        eye_to_source_scale_with_fov_fix = TanAnglesVec(
            2.0 / (lens_fov.periphery_fov_with_fix.left_tan + lens_fov.periphery_fov_with_fix.right_tan),
            2.0 / (lens_fov.periphery_fov_with_fix.up_tan + lens_fov.periphery_fov_with_fix.down_tan),
        )
        eye_to_source_offset_with_fov_fix = NDCVec(
            (lens_fov.periphery_fov_with_fix.left_tan - lens_fov.periphery_fov_with_fix.right_tan) /
                (lens_fov.periphery_fov_with_fix.left_tan + lens_fov.periphery_fov_with_fix.right_tan),
            (lens_fov.periphery_fov_with_fix.up_tan - lens_fov.periphery_fov_with_fix.down_tan) /
                (lens_fov.periphery_fov_with_fix.up_tan + lens_fov.periphery_fov_with_fix.down_tan),
        )

        return EyeToSourceFactors(
            lens_fov.periphery_fov,
            eye_to_source_scale,
            eye_to_source_offset,

            lens_fov.periphery_fov_with_fix,
            eye_to_source_scale_with_fov_fix,
            eye_to_source_offset_with_fov_fix,

            # TODO
            lens_fov.periphery_fov,
            lens_fov.periphery_fov,
            lens_fov.periphery_fov,
        )


@dataclass
class DistortionVars:
    image_count: int
    dimensions: DisplayDimensions
    scaling: DisplayScaling
    factors: Tuple[EyeToSourceFactors, EyeToSourceFactors]

    @staticmethod
    def from_params_eqn(params: HmdParams, eqn: DistortionEqn) -> DistortionVars:
        image_count = 1
        if params.render.double_buffer:
            image_count = 2
        elif any(x.type == 1 for x in params.displays):
            image_count = 2

        dimensions = DisplayDimensions.from_params(params)
        scaling = DisplayScaling.from_params(params, dimensions)

        eye_l = EyeToSourceFactors.from_params_scaling_eqn(
            params,
            scaling.eyes[0],
            0,
            eqn
        )
        eye_r = EyeToSourceFactors.from_params_scaling_eqn(
            params,
            scaling.eyes[1],
            1,
            eqn
        )
        factors = (eye_l, eye_r)

        return DistortionVars(
            image_count=image_count,
            dimensions=dimensions,
            scaling=scaling,
            factors=factors,
        )
