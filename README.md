# biapy-ops

[BiaPy](https://github.com/BiaPyX/BiaPy)'s model inference and
post-processing, as ops: plain Python functions declared with
[opspec](https://github.com/apposed/scikit-ops/tree/main/opspec), so a
runner can run them in their own environment and a front end can show them.

This is an example for BiaPy's authors as much as a collection: two ops, each
a thin wrapper over a BiaPy function that changes nothing about it, to show
what it takes to make one. Its sibling [tnia-ops](https://github.com/True-North-Intelligent-Algorithms/tnia-ops) does the same
for tnia-python.

Which parts of BiaPy should be ops, if any, is for BiaPy's developers to
decide. [`AGENTS.md`](AGENTS.md) explains how this repository is made, for
people and coding agents alike, and [`PROMPTS.md`](PROMPTS.md) has prompts
for redoing or extending it with one: picking other functions, adding an op,
moving the ops into BiaPy itself.

| Namespace | Ops |
|---|---|
| `predict` | `bmz` -- run any BioImage Model Zoo model (or BiaPy `.pth` checkpoint) on an image, via `BiaPy.load_workflow_from_model(...).predict(...)` |
| `segment` | `watershed_by_channels` -- turn predicted channels (F, C, B, D, P, ...) into instance labels, BiaPy's marker-controlled watershed |

Together they are a pipeline: `bmz(image, output="raw")` gives the network's
channels, and `watershed_by_channels` makes the labels, with thresholds that
can be tuned without running the network again.

```python
from biapy_ops.predict import bmz, Output
from biapy_ops.segment import watershed_by_channels

with oprunner.Runner() as runner:
    channels = runner.run(bmz, image=image, model="resourceful-otter", output=Output.raw)
    labels = runner.run(watershed_by_channels, prediction=channels,
                        channels="F,C", seed_thresholds="0.7,0.3")
```

## How an op is made

An op is a function with type hints, a docstring, and `@op(env=...)`.
`src/biapy_ops/segment/watershed_by_channels.py` is the whole pattern:

- The **signature** is the spec. `ImageOf`/`LabelsOf` say what an array is
  (a front end shows an image layer, a labels layer); `Axes("z?", "y", "x",
  "c")` says its axes; `Annotated[int, {"min": 0}]` bounds a widget; the
  docstring's `Args:` become the tooltips.
- **Imports of BiaPy go inside the function.** The op is declared in the
  front end's process, which has only opspec and numpy; it *runs* in the
  `biapy` environment.
- **Parameters a user sets, nothing else.** BiaPy's `cfg`, `save_dir`,
  `verbose` and `resolution` are fixed by the op, not exposed.

## Environments

One, `envs/biapy/pixi.toml`: BiaPy from PyPI, which brings its own PyTorch.

## Notes for BiaPy

Two things in BiaPy made an op hang when run in a worker. Both are worked
around here, and both are worth fixing in BiaPy:

- **`BiaPy(...)` replaces `sys.stdout` for the whole process** with a tee into
  its log buffer, and when it isn't verbose it never puts it back. An Appose
  worker answers its host on `sys.stdout`, so the answer to the call went into
  BiaPy's buffer and the host waited forever. `predict.bmz` puts the streams
  back after each BiaPy call (`_streams_kept`).
- **Importing BiaPy loads native extensions** (scipy's, cv2's, torch's). On
  Windows, loading one for the first time from an op's thread can deadlock;
  `watershed_by_channels` hung in `scipy.interpolate._fitpack`. So
  `envs/biapy/init.py` imports BiaPy on the worker's main thread at start-up.
  Not a BiaPy bug, but lazier module-level imports would shrink it.

Three small things in BiaPy would make these ops simpler or lighter:

1. **`predict(image, stage="raw")`.** `predict()` returns only the end
   result; `bmz(output=raw)` reads the network's output from
   `workflow._predictions`, a private field.
2. **Lazy imports in `biapy.data.post_processing`.** It imports torch, cv2,
   zarr, h5py and matplotlib at module level, so `watershed_by_channels`, plain
   scikit-image underneath, needs the full PyTorch environment.
3. **The channel codes as a public list.** The op takes `"F,C"` and has to
   know the valid codes; a constant BiaPy exports would let it check them.

## Next candidates

`utils.matching.matching` (instance metrics), `labels_into_channels`
(labels to training targets: the reverse of `watershed_by_channels`), and
`crappify` (degraded training pairs).

## Examples

`examples/bmz_then_watershed.ipynb` runs both ops with scikit-ops' runner on
scikit-image's `human_mitosis` nuclei: the model's raw F and C channels, then
labels from two threshold settings, then BiaPy's own end result. Its kernel:

```sh
uv sync
uv run python -m ipykernel install --user --name=biapy-ops-examples --display-name 'biapy-ops (examples)'
```

## In Fiji

With [fiji-skopkit](https://github.com/apposed/fiji-skopkit) installed in a
Fiji, both ops get commands of their own (`Plugins ▸ biapy-ops ▸ Predict ▸
Bmz`, `… ▸ Segment ▸ Watershed By Channels`) and are callable from scripts:

```python
from fiji_skopkit import skop
channels = skop.biapy_ops.predict.bmz(imp, output="raw")
labels = skop.biapy_ops.segment.watershed_by_channels(channels, seed_thresholds="0.7,0.3")
```

A script calls them by their collection's name, `skop.biapy_ops....`, and
`skop.predict.bmz` is refused with a message giving the full name. Every
collection's ops are named this way, so a script says whose op it runs: BiaPy
gets the credit for BiaPy's work, and two collections with a `predict.bmz`
never collide. The Log credits the environment the same way: "using
biapy-ops' biapy environment".

`fiji/script_templates/biapy-ops/` has two such scripts, which show in the
Script Editor under `Templates ▸ biapy-ops`, next to fiji-skopkit's own
`Templates ▸ scikit-ops`, and in the `Plugins ▸ biapy-ops` menu:

- `BiaPy_Model.py` -- any BioImage Model Zoo model on the open image; the
  result opens as a new image.
- `BiaPy_Nuclei_Watershed.py` -- the model's raw channels, then the watershed
  with thresholds from the dialog; the labels open as a new image.

One wrinkle: an op can't yet declare its *output's* axes (opspec's
`OutputSpec` has none), so Fiji names a result's axes after the input's. That
is right for labels, but `bmz(output="raw")` adds a channel axis, which Fiji
then calls "X". `BiaPy_Nuclei_Watershed.py` renames the axes itself; output
axes in opspec would make that unnecessary.

Fiji's host is Java, so it can't find a collection through Python entry
points; it is told, with `SKOP_COLLECTIONS` (a list of collection checkouts).
`fiji/start-fiji.bat C:\path\to\Fiji` sets it, and `SKOP_CHECKOUT`, to the
sibling checkouts, packs the templates into `Fiji\jars\biapy-ops-templates.jar`
(the Script Editor finds templates in jars, under `script_templates/`), copies
them to `Fiji\scripts\Plugins\biapy-ops` for the menu, and starts Fiji. This needs
fiji-skopkit from `main`, commit `bf6b35c` or later.

## Developing

```sh
uv sync
uv run pytest            # every op reads as a valid spec; no environment needed
uv run pytest -m env     # runs the ops: builds envs/biapy the first time
```
