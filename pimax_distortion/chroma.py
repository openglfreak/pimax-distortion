from typing import Tuple

from pimax_distortion.eqn import DistortionEqn, make_eqn
from pimax_distortion.params import HmdParams


class DistortionChroma(DistortionEqn):
    __slots__ = ('k', 'inner')
    k: Tuple[float, float, float, float, float, float]
    inner: DistortionEqn

    def __init__(
        self,
        k: Tuple[float, ...],
        inner: DistortionEqn,
    ):
        k = tuple(float(x) for x in k)  # type: ignore
        assert hasattr(inner, 'evaluate')
        n = len(k)
        if n < 1:
            raise ValueError('must have at least 1 coefficient')

        _k = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        if n > 4:
            _k[0:n] = k[0:n]
        else:
            _k[0:2] = k[0:2]
            if n > 2:
                _k[3:(n + 1)] = k[2:n]

        self.k = (_k[0], _k[1], _k[2], _k[3], _k[4], _k[5])
        self.inner = inner

    def evaluate(self, u: float, v: float) -> Tuple[float, float]:
        return self.inner.evaluate(u, v)

    def inverse_evaluate(self, u: float, v: float) -> Tuple[float, float]:
        return self.inner.inverse_evaluate(u, v)

    def evaluate_rgb(
        self,
        u: float,
        v: float
    ) -> Tuple[Tuple[float, float], Tuple[float, float], Tuple[float, float]]:
        k = tuple(float(x) for x in self.k)

        distance_squared = u * u + v * v
        distance_pow4 = distance_squared * distance_squared

        res_u, res_v = self.evaluate(u, v)
        rf = 1.0 + k[0] + k[1] * distance_squared + k[2] * distance_pow4
        bf = 1.0 + k[3] + k[4] * distance_squared + k[5] * distance_pow4
        return (
            (res_u * rf, res_v * rf),
            (res_u, res_v),
            (res_u * bf, res_v * bf),
        )


def make_chroma(params: HmdParams, eye: int) -> DistortionChroma:
    k = tuple(params.lenses[0].distortion_param.ChromaticAberration)

    eqn = make_eqn(params, eye)
    return DistortionChroma(k=k, inner=eqn)
