"""biapy-ops run by scikit-ops' runner, in the biapy environment.

These build envs/biapy the first time (PyTorch and BiaPy: several GB), and
the model test downloads resourceful-otter from the BioImage Model Zoo. Run
them with ``pytest -m env``; plain ``pytest`` skips them.
"""

import numpy as np
import pytest

oprunner = pytest.importorskip("oprunner")

from biapy_ops.predict import Output, bmz
from biapy_ops.segment import watershed_by_channels

pytestmark = pytest.mark.env


def two_touching_discs():
    """F and C channels as a network would predict them, for two discs that touch."""
    yy, xx = np.mgrid[:64, :96]
    a = (yy - 32) ** 2 + (xx - 30) ** 2
    b = (yy - 32) ** 2 + (xx - 66) ** 2
    foreground = ((a < 20**2) | (b < 20**2)).astype(np.float32)
    contour = (((a >= 17**2) & (a < 20**2)) | ((b >= 17**2) & (b < 20**2))).astype(np.float32)
    return np.stack([foreground, contour], axis=-1)


def test_watershed_splits_touching_objects():
    with oprunner.Runner() as runner:
        labels = runner.run(
            watershed_by_channels,
            prediction=two_touching_discs(),
            seed_thresholds="0.5,0.5",
            growth_mask_thresholds="0.5",
        )
    assert labels.shape == (64, 96)
    assert labels[32, 30] != labels[32, 66]
    assert set(np.unique(labels)) == {0, labels[32, 30], labels[32, 66]}


def test_bmz_raw_then_watershed():
    rng = np.random.default_rng(0)
    image = (rng.random((128, 128, 1)) * 255).astype(np.float32)
    with oprunner.Runner() as runner:
        channels = runner.run(bmz, image=image, output=Output.raw)
        assert channels.shape[:2] == (128, 128) and channels.shape[-1] == 2  # F, C
        labels = runner.run(watershed_by_channels, prediction=channels)
    assert labels.shape == (128, 128)
