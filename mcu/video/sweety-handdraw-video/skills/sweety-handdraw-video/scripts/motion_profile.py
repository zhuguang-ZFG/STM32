"""Shared pen-speed profiles: segment timing and pen-tip interpolation must use the same curve."""
import numpy as np

_TAU = np.linspace(0.0, 1.0, 513)
_MINJERK = 10 * _TAU**3 - 15 * _TAU**4 + 6 * _TAU**5


def _plateau(ramp=.2):
    """Cruise at constant speed with min-jerk speed-up/slow-down over the first and last 20% of the time."""
    speed = np.ones_like(_TAU)
    ease = lambda u: 10 * u**3 - 15 * u**4 + 6 * u**5
    speed[_TAU < ramp] = ease(_TAU[_TAU < ramp] / ramp)
    speed[_TAU > 1 - ramp] = ease((1 - _TAU[_TAU > 1 - ramp]) / ramp)
    distance = np.r_[0., np.cumsum((speed[1:] + speed[:-1]) / 2)]
    return distance / distance[-1]


_CURVES = {'minjerk': _MINJERK, 'plateau': _plateau()}
# Peak speed relative to the mean speed of each profile (limits how fast a stroke may be timed).
PEAK = {'linear': 1., 'minjerk': 1.875, 'plateau': float(np.diff(_CURVES['plateau']).max() * (len(_TAU) - 1))}


def distance_fraction(time_fraction, profile='linear'):
    """Fraction of stroke length covered after this fraction of the stroke's time."""
    time_fraction = np.clip(time_fraction, 0.0, 1.0)
    if profile in _CURVES:
        return np.interp(time_fraction, _TAU, _CURVES[profile])
    return time_fraction


def time_fraction(distance_fraction_value, profile='linear'):
    """Inverse of distance_fraction: when the tip reaches this fraction of the stroke length."""
    distance_fraction_value = np.clip(distance_fraction_value, 0.0, 1.0)
    if profile in _CURVES:
        return np.interp(distance_fraction_value, _CURVES[profile], _TAU)
    return distance_fraction_value
