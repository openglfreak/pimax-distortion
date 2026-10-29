# pyright: strict

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    type _Number = int | float | np.integer | np.floating
else:
    type _Number = int | float


@dataclass
class MetersRect:
    up_m: _Number = 0.0
    down_m: _Number = 0.0
    left_m: _Number = 0.0
    right_m: _Number = 0.0


@dataclass
class NDCRect:
    up_ndc: _Number = 0.0
    down_ndc: _Number = 0.0
    left_ndc: _Number = 0.0
    right_ndc: _Number = 0.0


@dataclass
class AnglesRect:
    up_rad: _Number = 0.0
    down_rad: _Number = 0.0
    left_rad: _Number = 0.0
    right_rad: _Number = 0.0


@dataclass
class TanAnglesRect:
    up_tan: _Number = 0.0
    down_tan: _Number = 0.0
    left_tan: _Number = 0.0
    right_tan: _Number = 0.0


@dataclass
class NDCAnglesRect:
    up_ndc: _Number = 0.0
    down_ndc: _Number = 0.0
    left_ndc: _Number = 0.0
    right_ndc: _Number = 0.0
