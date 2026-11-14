"""Instances from a network's channels: BiaPy's marker-controlled watershed.

BiaPy's instance models don't predict labels; they predict channels -- F
(foreground), C (contours), B, D (distances), P (centre points) and more --
and BiaPy turns them into labels with a watershed: seeds from thresholding
some channels, a mask to grow them in from others, and one channel as the
surface they flood. This op is that last step on its own, so the thresholds
can be tuned on a prediction without running the network again.

The channel lists are comma-separated strings ("F,C") rather than lists, so a
front end can show them as one text box.
"""

from typing import Annotated

import numpy as np
from opspec.op import Axes, op
from opspec.runtime import progress
from opspec.types import ImageOf, LabelsOf


@op(env="biapy")
def watershed_by_channels(
    prediction: Annotated[ImageOf[np.ndarray], Axes("z?", "y", "x", "c")],
    channels: str = "F,C",
    seed_channels: str = "F,C",
    seed_thresholds: str = "auto,auto",
    growth_mask_channels: str = "F",
    growth_mask_thresholds: str = "auto",
    topographic_surface: str = "F",
    min_seed_size: Annotated[int, {"min": 0, "max": 100000}] = 0,
    by_2d_slices: bool = False,
) -> LabelsOf[np.ndarray]:
    """Turn predicted channels into instance labels, by watershed.

    Args:
        prediction: The network's output, channels last: e.g. predict.bmz
            with ``output=raw``.
        channels: What each channel of ``prediction`` is, in order, by
            BiaPy's codes: F foreground, C contours, B, D, Db, P points, ...
        seed_channels: The channels thresholded to make the seeds.
        seed_thresholds: One per seed channel: a number, or ``auto`` for Otsu.
        growth_mask_channels: The channels thresholded to make the mask the
            seeds grow in.
        growth_mask_thresholds: One per growth mask channel: a number, or
            ``auto`` for half of Otsu.
        topographic_surface: The channel the seeds flood.
        min_seed_size: Seeds smaller than this many pixels are dropped before
            the watershed; 0 keeps them all.
        by_2d_slices: For a stack, run the watershed plane by plane, so
            instances can't spill into each other along z.
    """
    from biapy.data.post_processing.post_processing import (
        watershed_by_channels as biapy_watershed,
    )

    data_channels = _names(channels)
    seeds, seed_ths = _names(seed_channels), _thresholds(seed_thresholds)
    growth, growth_ths = _names(growth_mask_channels), _thresholds(growth_mask_thresholds)
    _check(prediction, data_channels, seeds, seed_ths, growth, growth_ths, topographic_surface)

    progress("Watershed")
    return biapy_watershed(
        data=prediction,
        channels=data_channels,
        seed_channels=seeds,
        seed_channel_ths=seed_ths,
        topo_surface_channel=topographic_surface.strip(),
        growth_mask_channels=growth,
        growth_mask_channel_ths=growth_ths,
        remove_before=min_seed_size > 0,
        thres_small_before=min_seed_size,
        watershed_by_2d_slices=by_2d_slices,
        verbose=False,
    )


def _names(text: str) -> list[str]:
    return [s.strip() for s in text.split(",") if s.strip()]


def _thresholds(text: str) -> list[float | str]:
    return [s if s == "auto" else float(s) for s in _names(text)]


def _check(prediction, channels, seeds, seed_ths, growth, growth_ths, surface):
    """Fail with a message a user can act on, before BiaPy fails with one they can't."""
    if prediction.shape[-1] != len(channels):
        raise ValueError(
            f"prediction has {prediction.shape[-1]} channels but {len(channels)} are "
            f"named ({','.join(channels)})"
        )
    for what, names in (("seed", seeds), ("growth mask", growth), ("surface", [surface.strip()])):
        missing = [n for n in names if n not in channels]
        if missing:
            raise ValueError(f"{what} channel(s) {missing} are not in channels {channels}")
    if len(seed_ths) != len(seeds):
        raise ValueError(f"{len(seeds)} seed channels but {len(seed_ths)} seed thresholds")
    if len(growth_ths) != len(growth):
        raise ValueError(f"{len(growth)} growth mask channels but {len(growth_ths)} thresholds")
