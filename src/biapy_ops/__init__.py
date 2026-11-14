"""BiaPy's model inference and post-processing, as ops.

Ops are grouped into namespaces by what they do, laid out like scikit-ops':
a namespace scikit-ops has as a folder (``segment``) is a folder here too,
one module per op; any other is a single module (``predict.py``). Either
way they are imported from the namespace::

    from biapy_ops.predict import bmz
    from biapy_ops.segment import watershed_by_channels

Heavy imports, BiaPy's included, stay inside the op functions, so reading
these ops needs only opspec and numpy.
"""

__version__ = "0.1.0.dev0"
