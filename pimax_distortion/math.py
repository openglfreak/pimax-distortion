# pyright: strict

import math
from typing import TYPE_CHECKING, Tuple, overload

from pimax_distortion.recttypes import TanAnglesRect

if TYPE_CHECKING:
    import numpy as np


@overload
def tangent_add(a: int | float, b: int | float) -> float: ...
@overload
def tangent_add(a: int | float, b: np.integer | np.floating) -> np.floating: ...
@overload
def tangent_add(a: np.integer | np.floating, b: int | float) -> np.floating: ...
@overload
def tangent_add(a: np.integer | np.floating, b: np.integer | np.floating) -> np.floating: ...

def tangent_add(a, b):  # pyright: ignore[reportUnknownParameterType]
    return (a + b) / (1 - a * b)  # pyright: ignore[reportUnknownVariableType]


def apply_extra_fov(
    eye: int,
    fov: TanAnglesRect,
    extra_fov: Tuple[float, float, float, float],
) -> TanAnglesRect:
    up = math.tan(math.radians(extra_fov[0]))
    down = math.tan(math.radians(extra_fov[1]))
    left = math.tan(math.radians(extra_fov[2]))
    right = math.tan(math.radians(extra_fov[3]))

    if eye == 1:
        left, right = right, left

    return TanAnglesRect(
        tangent_add(fov.up_tan, up),
        tangent_add(fov.down_tan, down),
        tangent_add(fov.left_tan, left),
        tangent_add(fov.right_tan, right),
    )
