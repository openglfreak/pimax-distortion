# pyright: strict

from typing import TYPE_CHECKING, Tuple, TypeVar, Union

from pimax_distortion.params import HmdRenderEyeRotation


if TYPE_CHECKING:
    import numpy as np

    _T = TypeVar('_T', bound=Union[int, float, np.integer, np.inexact])
else:
    _T = Union[int, float]


def rotate(u: _T, v: _T, rot: HmdRenderEyeRotation) -> Tuple[_T, _T]:
    if rot == HmdRenderEyeRotation.R_0:
        return u, v
    elif rot == HmdRenderEyeRotation.R_90:
        return type(v)(-v), u
    elif rot == HmdRenderEyeRotation.R_180:
        return type(u)(-u), type(v)(-v)
    elif rot == HmdRenderEyeRotation.R_270:
        return v, type(u)(-u)
    assert False and 'invalid rotation'
