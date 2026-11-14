"""Every op reads as a valid spec. No environment needed."""

import importlib
import pkgutil

import pytest
from opspec.op import OpSpec, is_op

import biapy_ops


def all_ops():
    for info in pkgutil.walk_packages(biapy_ops.__path__, "biapy_ops."):
        if info.name.rsplit(".", 1)[-1].startswith("_"):
            continue
        module = importlib.import_module(info.name)
        for name, value in vars(module).items():
            if is_op(value) and value.__module__ == module.__name__:
                yield f"{info.name}:{name}", value


OPS = dict(all_ops())


def test_there_are_ops():
    assert sorted(OPS) == [
        "biapy_ops.predict:bmz",
        "biapy_ops.segment.watershed_by_channels:watershed_by_channels",
    ]


@pytest.mark.parametrize("name", sorted(OPS))
def test_each_op_reads_as_a_spec(name):
    spec = OpSpec.from_op(OPS[name])
    assert spec.env == "biapy"
    assert spec.outputs
    assert OpSpec.from_dict(spec.to_dict()).name == spec.name


def test_watershed_rejects_a_mismatch_before_biapy_sees_it():
    from biapy_ops.segment.watershed_by_channels import _check, _thresholds

    prediction = __import__("numpy").zeros((8, 8, 2))
    assert _thresholds("auto, 0.5") == ["auto", 0.5]
    with pytest.raises(ValueError, match="2 channels but 3"):
        _check(prediction, ["F", "C", "D"], ["F"], ["auto"], ["F"], ["auto"], "F")
    with pytest.raises(ValueError, match="not in channels"):
        _check(prediction, ["F", "C"], ["P"], ["auto"], ["F"], ["auto"], "F")
    with pytest.raises(ValueError, match="seed thresholds"):
        _check(prediction, ["F", "C"], ["F", "C"], ["auto"], ["F"], ["auto"], "F")
