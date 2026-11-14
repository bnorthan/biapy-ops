"""Running a trained model: any BioImage Model Zoo model BiaPy can load.

``bmz`` wraps BiaPy's own two-line API::

    biapy = BiaPy.load_workflow_from_model(model)
    prediction = biapy.predict(image)

BiaPy reads the workflow (instance segmentation, denoising, super-resolution,
...) and its pre- and post-processing from the model's RDF, so the op needs
nothing but the image and the model's name.
"""

import sys
from contextlib import contextmanager
from enum import Enum
from typing import Annotated

import numpy as np
from opspec.op import Axes, op
from opspec.runtime import progress
from opspec.types import ImageOf

# Loaded models, kept warm across calls in the same worker: loading means
# downloading (once) and building the network (every time).
_models: dict = {}


class Output(Enum):
    """Which of BiaPy's results to return."""

    #: What BiaPy's predict() returns: the workflow's end result, e.g.
    #: instance labels for an instance segmentation model.
    final = "final"
    #: The network's output, before BiaPy's post-processing: e.g. the
    #: foreground and contour channels an instance model predicts, ready for
    #: watershed_by_channels with thresholds of your own.
    raw = "raw"


@op(env="biapy")
def bmz(
    image: Annotated[ImageOf[np.ndarray], Axes("z?", "y", "x", "c?")],
    model: str = "resourceful-otter",
    output: Output = Output.final,
    use_gpu: bool = True,
) -> ImageOf[np.ndarray]:
    """Run a BioImage Model Zoo model, or a BiaPy checkpoint, on an image.

    Args:
        image: A 2D image, or a 3D stack for a 3D model; channels last.
        model: A BioImage Model Zoo id or nickname (downloaded and cached on
            first use), or the path to a BiaPy ``.pth`` checkpoint. The
            default, resourceful-otter, is a 2D nuclei instance segmentation
            model predicting foreground and contour channels (F, C).
        output: ``final`` for BiaPy's end result, ``raw`` for the network's
            own output before post-processing.
        use_gpu: Run on the first GPU when there is one.
    """
    import torch
    from biapy import BiaPy

    gpu = "0" if use_gpu and torch.cuda.is_available() else ""
    key = (model, gpu)
    if key not in _models:
        progress(f"Loading {model}")
        # No result_dir: BiaPy runs ephemerally and writes nothing to disk.
        with _streams_kept():
            _models[key] = BiaPy.load_workflow_from_model(model, gpu=gpu)
    biapy = _models[key]

    progress(f"Predicting with {model}")
    with _streams_kept():
        final = biapy.predict(image)
    if output is Output.final:
        return final

    # predict() returns only the end result. The network's output is the
    # first "raw" entry BiaPy recorded on the way there -- a private field.
    # TODO(BiaPy): a public way to ask predict() for it, e.g. predict(image,
    # stage="raw"), would make this two lines.
    raw = next(p["data"] for p in biapy.workflow._predictions if p.get("role") == "raw")
    if raw.ndim >= 1 and raw.shape[0] == 1:  # the batch axis, as predict() drops it
        raw = raw[0]
    return raw


@contextmanager
def _streams_kept():
    """Put sys.stdout, sys.stderr and print back however BiaPy leaves them.

    A worker answers its host by printing one JSON line per message on
    sys.stdout. BiaPy changes both halves of that, process-wide, and keeps
    them changed:

    - Building a BiaPy replaces sys.stdout with a tee into its own log
      buffer, so the answers went into the buffer.
    - Preparing a model replaces ``builtins.print`` with a timestamping one
      (``biapy.utils.misc.setup_for_distributed``), so each answer started
      with "[10:43:07.348699] " and the host could not read it.

    Either way the host waited forever. TODO(BiaPy): don't replace process
    globals when used as a library, or restore them when a call returns.
    """
    import builtins

    out, err, printer = sys.stdout, sys.stderr, builtins.print
    try:
        yield
    finally:
        sys.stdout, sys.stderr, builtins.print = out, err, printer
