# pyright: strict

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np

    type _Number = float | np.floating
else:
    type _Number = int | float


@dataclass
class Quaternion:
    x: _Number = 0.0
    y: _Number = 0.0
    z: _Number = 0.0
    w: _Number = 0.0


@dataclass
class Vector3:
    x: _Number = 0.0
    y: _Number = 0.0
    z: _Number = 0.0


@dataclass
class Pose:
    orientation: Quaternion = Quaternion()
    position: Vector3 = Vector3()
