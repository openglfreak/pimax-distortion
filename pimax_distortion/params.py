import collections
import collections.abc
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Any, Callable, List, Optional, Tuple


class HmdDisplayType(IntEnum):
    None_= 0
    stream = 5
    airlink = 6
    stream_direct = 7


class HmdDisplayScanDirection(IntEnum):
    RL = 0
    TB = 1
    LR = 2
    BT = 3


class HmdDisplayShutterType(IntEnum):
    rolling = 0
    global_ = 1


@dataclass
class HmdDisplayVariantParams:
    width: int
    height: int
    refresh_rate: float
    v_size: float
    h_size: float
    gap: float
    dynamic_gap: bool
    pixel_settle_time: float
    num_modes: int
    num_modes_min: int

    @staticmethod
    def from_dict(data: dict) -> HmdDisplayVariantParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        get_with_default('width', 0)
        get_with_default('height', 0)
        get_with_default('refresh_rate', 0.0)
        get_with_default('v_size', 0.0)
        get_with_default('h_size', 0.0)
        get_with_default('gap', 0.0)
        get_with_default('dynamic_gap', False)
        get_with_default('pixel_settle_time', 0.0)
        get_with_default('num_modes', 0)
        get_with_default('num_modes_min', 0)

        return HmdDisplayVariantParams(**params)


@dataclass
class HmdDisplayParams:
    type: HmdDisplayType
    width: int
    height: int
    refresh_rate: float
    refresh_rate_check: bool
    native_width: int
    native_height: int
    num_modes: int
    num_modes_min: int
    edid_vid: int
    edid_pid: int
    ext_edid_vids: List[int]
    ext_edid_pids: List[int]
    display_scan_dir: HmdDisplayScanDirection
    display_shutter_type: HmdDisplayShutterType
    h_size: float
    v_size: float
    r_gap: float
    gap: Tuple[float, float]
    pixel_settle_time: float
    pixel_persist_time: float
    variants: List[HmdDisplayVariantParams]

    @staticmethod
    def from_dict(data: dict) -> HmdDisplayParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def get_enum(name: str, enum: type[Enum]):
            nonlocal params
            _value = data.get(name)
            if _value is not None:
                params[name] = enum[_value]
            else:
                params[name] = enum(0)

        get_enum('type', HmdDisplayType)
        get_with_default('width', 0)
        get_with_default('height', 0)
        get_with_default('refresh_rate', 0.0)
        get_with_default('refresh_rate_check', True)
        get_with_default('native_width', 0)
        get_with_default('native_height', 0)
        get_with_default('num_modes', 0)
        get_with_default('num_modes_min', 0)
        get_with_default('edid_vid', 0)
        get_with_default('edid_pid', 0)
        get_with_default('ext_edid_vids', [])
        get_with_default('ext_edid_pids', [])
        get_enum('display_scan_dir', HmdDisplayScanDirection)
        _display_shutter_type = data.get('display_shutter_type')
        if _display_shutter_type is not None:
            if _display_shutter_type == 'global':
                _display_shutter_type = 'global_'
            params['display_shutter_type'] = \
                HmdDisplayShutterType[_display_shutter_type]
        else:
            params['display_shutter_type'] = HmdDisplayShutterType(0)
        get_with_default('h_size', 0.1296)
        get_with_default('v_size', 0.0729)
        get_with_default('r_gap', 0.0)
        get_with_default('gap', 0.0, cast=lambda x: (x, x))
        get_with_default('pixel_settle_time', 1.0)
        get_with_default('pixel_persist_time', 1.0)
        _variants = data.get('variants', [])
        params['variants'] = \
            list(HmdDisplayVariantParams.from_dict(x) for x in _variants)

        return HmdDisplayParams(**params)


class HmdLensDistortionEqn(IntEnum):
    None_ = 0
    CatmullRom10 = 1
    Poly4 = 2
    PointSamples = 4
    CatmullRom17 = 5
    CatmullRom10Inv = 6
    CatmullRom17Inv = 7


@dataclass
class HmdLensDistortionParams:
    eqn: HmdLensDistortionEqn
    K: List[float]
    K_x_off_o: Optional[List[float]]
    K_x_off_i: Optional[List[float]]
    # Read from file
    PointSamplesFile: List[float]
    ChromaticAberration: List[float]
    MaxRadius: float
    MinRadius: float
    EyeRelief: float

    @staticmethod
    def default() -> HmdLensDistortionParams:
        return HmdLensDistortionParams(
            eqn=HmdLensDistortionEqn.CatmullRom10,
            K=[
                1.0,
                1.0425,
                1.0826,
                1.13,
                1.185,
                1.25,
                1.338,
                1.455,
                1.62,
                1.84,
                2.2,
            ],
            K_x_off_o=None,
            K_x_off_i=None,
            PointSamplesFile=[],
            ChromaticAberration=[
                -0.006,
                0.0,
                0.014,
                0.0
            ],
            MaxRadius=1.0,
            MinRadius=0.0,
            EyeRelief=0.0,
        )

    @staticmethod
    def from_dict(data: dict) -> HmdLensDistortionParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def get_enum(name: str, enum: type[Enum]):
            nonlocal params
            _value = data.get(name)
            if _value is not None:
                params[name] = enum[_value]
            else:
                params[name] = enum(0)

        get_enum('eqn', HmdLensDistortionEqn)
        get_with_default('K', [])
        get_with_default('K_x_off_o', None)
        get_with_default('K_x_off_i', None)
        params['PointSamplesFile'] = []
        get_with_default('ChromaticAberration', [])
        get_with_default('MaxRadius', 0.0)
        get_with_default('MinRadius', 0.0)
        get_with_default('EyeRelief', 0.0)

        return HmdLensDistortionParams(**params)


@dataclass
class HmdLensParams:
    separation: float
    adc_to_separation_K: Tuple[float, float]
    v_center_off: Tuple[float, float]
    diameter: float
    inner_diameter: float
    MetersPerTanAngleAtCenter: float
    BackSufaceToDisplayDistance: float
    ipd_offset: float
    periphery_diameter: float
    distortion_param: HmdLensDistortionParams
    periphery_distortion_param: HmdLensDistortionParams
    back_surface_param: HmdLensDistortionParams
    periphery_render_type: int

    @staticmethod
    def from_dict(data: dict) -> HmdLensParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def get_dataclass(name: str, cls: type):
            nonlocal params
            _value = data.get(name, {})
            params[name] = cls.from_dict(_value)

        get_with_default('separation', 0.06862)
        get_with_default('adc_to_separation_K', (0.0, 1.0), cast=tuple)
        get_with_default('v_center_off', 0.0, cast=lambda x: (x, x))
        get_with_default('diameter', 0.035)
        get_with_default('inner_diameter', 0.0)
        get_with_default('MetersPerTanAngleAtCenter', 0.0425)
        get_with_default('BackSufaceToDisplayDistance', 0.04)
        get_with_default('ipd_offset', 0.0)
        get_with_default('periphery_diameter', 0.0)
        if 'distortion_param' in data:
            get_dataclass('distortion_param', HmdLensDistortionParams)
        else:
            params['distortion_param'] = HmdLensDistortionParams.default()
        if 'periphery_distortion_param' in data:
            get_dataclass('periphery_distortion_param', HmdLensDistortionParams)
        else:
            params['periphery_distortion_param'] = HmdLensDistortionParams.default()
        get_dataclass('back_surface_param', HmdLensDistortionParams)
        get_with_default('periphery_render_type', 0)

        return HmdLensParams(**params)


class HmdRenderAirlinkStreamFoveatedEncoding(IntEnum):
    None_ = 0
    roi = 1
    quad_views = 2


class HmdRenderEyeRotation(IntEnum):
    R_0 = 0
    R_90 = 1
    R_180 = 2
    R_270 = 3

    def inverse(self) -> HmdRenderEyeRotation:
        if self in (HmdRenderEyeRotation.R_0, HmdRenderEyeRotation.R_180):
            return self
        elif self == HmdRenderEyeRotation.R_90:
            return HmdRenderEyeRotation.R_270
        elif self == HmdRenderEyeRotation.R_270:
            return HmdRenderEyeRotation.R_90
        else:
            assert False and 'invalid enum value'


class HmdRenderEyeViewPort(IntEnum):
    top = 0
    left = 1
    bottom = 2
    right = 3
    full = 4


@dataclass
class HmdRenderEyeParams:
    fov_fix_degree: float
    lens_fix_degree: float
    rotate: HmdRenderEyeRotation
    distortion_enable: bool
    view_port: HmdRenderEyeViewPort
    extra_predict_time: float

    @staticmethod
    def from_dict(data: dict) -> HmdRenderEyeParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def get_enum(name: str, enum: type[Enum]):
            nonlocal params
            _value = data.get(name)
            if _value is not None:
                params[name] = enum[_value]
            else:
                params[name] = enum(0)

        get_with_default('fov_fix_degree', 0.0)
        get_with_default('lens_fix_degree', 0.0)
        _rotate = data.get('rotate', 0)
        params['rotate'] = HmdRenderEyeRotation['R_' + str(_rotate)]
        get_with_default('distortion_enable', False)
        get_enum('view_port', HmdRenderEyeViewPort)
        get_with_default('extra_predict_time', 0.0)

        return HmdRenderEyeParams(**params)


@dataclass
class HmdRenderEyeHiddenAreaParams:
    enable: bool
    triangle_split_to: int
    triangles: List[float]
    triangles_fix: List[float]
    triangles_custom_fov: List[float]
    triangles_fix_custom_fov: List[float]

    @staticmethod
    def from_dict(data: dict) -> HmdRenderEyeHiddenAreaParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        get_with_default('enable', False)
        get_with_default('triangle_split_to', 0)
        get_with_default('triangles', [])
        get_with_default('triangles_fix', [])
        get_with_default('triangles_custom_fov', [])
        get_with_default('triangles_fix_custom_fov', [])

        return HmdRenderEyeHiddenAreaParams(**params)


@dataclass
class HmdRendeFOVParams:
    default_fov_level: float
    extra: Tuple[float, float, float, float]
    extra_fix: Tuple[float, float, float, float]

    @staticmethod
    def from_dict(data: dict) -> HmdRendeFOVParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def to_tuple4f(x: Tuple[float, ...]) -> Tuple[float, float, float, float]:
            assert len(x) <= 4
            return (*x, 0.0, 0.0, 0.0, 0.0)[:4]  # type: ignore

        get_with_default('default_fov_level', 0.0)
        get_with_default('extra', (0.0, 0.0, 0.0, 0.0), cast=to_tuple4f)
        get_with_default('extra_fix', (0.0, 0.0, 0.0, 0.0), cast=to_tuple4f)

        return HmdRendeFOVParams(**params)


@dataclass
class HmdRenderOverDriveParams:
    ...

    @staticmethod
    def from_dict(data: dict) -> HmdRenderOverDriveParams:
        return HmdRenderOverDriveParams()


@dataclass
class HmdRenderParams:
    double_buffer: bool
    allow_extend_mode: bool
    switch_to_2k_when_1k_on_amd: bool
    enable_corner_tag: bool
    pixels_per_tan_angle_at_center_rate: float
    lens_separation_to_ipd_rate: float
    force_parallel_projection_on: bool
    disable_atw: bool
    airlink_stream_fovated_encoding: HmdRenderAirlinkStreamFoveatedEncoding
    eyes: Tuple[HmdRenderEyeParams, HmdRenderEyeParams]
    hidden_area: HmdRenderEyeHiddenAreaParams
    local_dimming_enable: bool
    local_dimming_cols_per_eye: int
    local_dimming_rows_per_eye: int
    local_dimming_disabled_backlight: int
    fov: HmdRendeFOVParams
    over_drive: HmdRenderOverDriveParams

    @staticmethod
    def from_dict(data: dict) -> HmdRenderParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def get_enum(name: str, enum: type[Enum]):
            nonlocal params
            _value = data.get(name)
            if _value is not None:
                params[name] = enum[_value]
            else:
                params[name] = enum(0)

        def get_dataclass(name: str, cls: type):
            nonlocal params
            _value = data.get(name, {})
            params[name] = cls.from_dict(_value)

        get_with_default('double_buffer', False)
        get_with_default('allow_extend_mode', False)
        get_with_default('switch_to_2k_when_1k_on_amd', False)
        get_with_default('enable_corner_tag', False)
        get_with_default('pixels_per_tan_angle_at_center_rate', 0.0)
        get_with_default('lens_separation_to_ipd_rate', 0.0)
        get_with_default('force_parallel_projection_on', False)
        get_with_default('disable_atw', False)
        get_enum('airlink_stream_fovated_encoding',
                 HmdRenderAirlinkStreamFoveatedEncoding)
        _eyes = data.get('eyes', [{}, {}])
        params['eyes'] = tuple(HmdRenderEyeParams.from_dict(x) for x in _eyes)
        get_dataclass('hidden_area', HmdRenderEyeHiddenAreaParams)
        get_with_default('local_dimming_enable', False)
        get_with_default('local_dimming_cols_per_eye', 0)
        get_with_default('local_dimming_rows_per_eye', 0)
        get_with_default('local_dimming_disabled_backlight', 0)
        get_dataclass('fov', HmdRendeFOVParams)
        get_dataclass('over_drive', HmdRenderOverDriveParams)

        return HmdRenderParams(**params)


@dataclass
class HmdParams:
    format_ver: int
    name: str
    display_name: str
    product: str
    usb_vid: int
    usb_pid: int
    usb_intf: int
    uvc_vid: int
    uvc_pid: int
    localdimming_vid: int
    localdimming_pid: int
    default_eye_relief: int
    imu_fix_degree: int
    use_tracker: str
    hmd_type: str
    has_hmd_controller: bool
    has_physical_ipd_adjust: bool
    has_motor_ipd_adjust: bool
    has_eyetracking: bool
    support_eye_tracking_toggle: bool
    support_controller_pair: bool
    need_keep_display_alive: bool
    support_hmd_standby_mode: bool
    support_hmd_bl_open_close: bool
    support_hmd_brainwarp: bool
    support_hmd_parallel_projection_led_indicator: bool
    support_hmd_volume_adjust: bool
    support_screen_saver: bool
    support_proximity_sensor: bool
    support_vst: bool
    support_ipd_shortcut_adjust: bool
    support_hand_tracking: bool
    support_lighthouse_3dof_support: bool
    ipd_guide_left_target_position_x: int
    default_display_timing_selection: int
    lens_type_dynamic_retrieve: bool
    lens_id_match_ignore_lens_type: bool
    lens_id_match_lens_type: int
    lens_id_match_panel_type: int
    lens_separation_fixed: bool
    lens_render_info_dynamic_retrieve: bool
    support_dp_cable_reset: bool
    lens_separation_level_offsets: List[float]
    max_physical_ipd: float
    min_physical_ipd: float
    q_d2i: Tuple[float, float, float, float]
    t_d2i: Tuple[float, float, float]
    hmd_keys_enable: bool
    hmd_keys_power: int
    hmd_keys_volume_up: int
    hmd_keys_volume_down: int
    hmd_keys_capacity: int
    gpu_driver_check_info_enable: bool
    gpu_driver_check_info_min_bridge_ver: int
    min_firmware_version: str
    audio_match: List[str]
    bridge_ver_check: bool
    bridge_ver: int
    displays: List[HmdDisplayParams]
    lenses: List[HmdLensParams]
    render: HmdRenderParams

    @staticmethod
    def from_dict(data: dict) -> HmdParams:
        params = {}

        def get_with_default(name: str, dflt: Any,
                             cast: Callable[[Any], Any] = lambda x: x):
            nonlocal params
            params[name] = cast(data.get(name, dflt))

        def get_dataclass(name: str, cls: type):
            nonlocal params
            _value = data.get(name, {})
            params[name] = cls.from_dict(_value)

        get_with_default('format_ver', 0)
        get_with_default('name', '')
        get_with_default('display_name', '')
        get_with_default('product', '')
        get_with_default('usb_vid', 0)
        get_with_default('usb_pid', 0)
        get_with_default('usb_intf', 0)
        get_with_default('uvc_vid', 0)
        get_with_default('uvc_pid', 0)
        get_with_default('localdimming_vid', 0)
        get_with_default('localdimming_pid', 0)
        get_with_default('default_eye_relief', 0)
        get_with_default('imu_fix_degree', 0)
        get_with_default('use_tracker', '')
        get_with_default('hmd_type', '')
        get_with_default('has_hmd_controller', False)
        get_with_default('has_physical_ipd_adjust', False)
        get_with_default('has_motor_ipd_adjust', False)
        get_with_default('has_eyetracking', False)
        get_with_default('support_eye_tracking_toggle', False)
        get_with_default('support_controller_pair', False)
        get_with_default('need_keep_display_alive', False)
        get_with_default('support_hmd_standby_mode', False)
        get_with_default('support_hmd_bl_open_close', False)
        get_with_default('support_hmd_brainwarp', False)
        get_with_default('support_hmd_parallel_projection_led_indicator', False)
        get_with_default('support_hmd_volume_adjust', False)
        get_with_default('support_screen_saver', False)
        get_with_default('support_proximity_sensor', False)
        get_with_default('support_vst', False)
        get_with_default('support_ipd_shortcut_adjust', False)
        get_with_default('support_hand_tracking', False)
        get_with_default('support_lighthouse_3dof_support', False)
        get_with_default('ipd_guide_left_target_position_x', 0)
        get_with_default('default_display_timing_selection', 0)
        get_with_default('lens_type_dynamic_retrieve', False)
        get_with_default('lens_id_match_ignore_lens_type', False)
        get_with_default('lens_id_match_lens_type', 0)
        get_with_default('lens_id_match_panel_type', 0)
        get_with_default('lens_separation_fixed', False)
        get_with_default('lens_render_info_dynamic_retrieve', False)
        get_with_default('support_dp_cable_reset', False)
        get_with_default('lens_separation_level_offsets', [])
        get_with_default('max_physical_ipd', 0.0)
        get_with_default('min_physical_ipd', 0.0)
        get_with_default('q_d2i', (0.0, 0.0, 0.0, 1.0), cast=tuple)
        get_with_default('t_d2i', (0.0, 0.0, 0.0), cast=tuple)
        get_with_default('hmd_keys_enable', False)
        get_with_default('hmd_keys_power', 0)
        get_with_default('hmd_keys_volume_up', 0)
        get_with_default('hmd_keys_volume_down', 0)
        get_with_default('hmd_keys_capacity', 0)
        get_with_default('gpu_driver_check_info_enable', False)
        get_with_default('gpu_driver_check_info_min_bridge_ver', 0)
        get_with_default('min_firmware_version', '')
        get_with_default('audio_match', [])
        get_with_default('bridge_ver_check', False)
        get_with_default('bridge_ver', 0)
        _displays = data.get('displays', [])
        params['displays'] = \
            list(HmdDisplayParams.from_dict(x) for x in _displays)
        _lens = data.get('lens', [])
        if isinstance(_lens, collections.abc.Mapping):
            params['lenses'] = [HmdLensParams.from_dict(dict(_lens))]
        else:
            params['lenses'] = list(HmdLensParams.from_dict(x) for x in _lens)
        get_dataclass('render', HmdRenderParams)

        return HmdParams(**params)
