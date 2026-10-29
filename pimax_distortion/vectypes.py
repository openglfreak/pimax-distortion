# pyright: strict

from dataclasses import dataclass

from typing import TYPE_CHECKING

from pimax_distortion.ndc import from_ndc_uv, to_ndc_uv

if TYPE_CHECKING:
    import numpy as np

    type _Number = float | np.floating
else:
    type _Number = int | float


@dataclass
class MetersVec:
    u_m: _Number = 0.0
    v_m: _Number = 0.0


@dataclass
class UV01Vec:
    u_01: _Number = 0.0
    v_01: _Number = 0.0

    def to_ndc(self) -> NDCVec:
        u_ndc, v_ndc = to_ndc_uv(self.u_01, self.v_01)
        return NDCVec(u_ndc, v_ndc)


@dataclass
class NDCVec:
    u_ndc: _Number = 0.0
    v_ndc: _Number = 0.0

    def to_01(self) -> UV01Vec:
        u_01, v_01 = from_ndc_uv(self.u_ndc, self.v_ndc)
        return UV01Vec(u_01, v_01)


@dataclass
class AnglesVec:
    u_rad: _Number = 0.0
    v_rad: _Number = 0.0


@dataclass
class TanAnglesVec:
    u_tan: _Number = 0.0
    v_tan: _Number = 0.0


@dataclass
class NDCAnglesVec:
    u_ndc: _Number = 0.0
    v_ndc: _Number = 0.0
