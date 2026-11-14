# Prompts for BiaPy's developers

This repository is a sketch: two of BiaPy's functions as ops, to show what it
takes. Which parts of BiaPy should be ops -- and whether ops are worth it at
all -- is your call. If you want to try, these prompts are a starting point
for a coding agent (Claude Code, Codex, Copilot, ...). Each assumes the agent
can read this repository; `AGENTS.md` tells it how the repository works and
what to watch out for.

Edit them freely. The words in `<angle brackets>` are yours to fill in.

## 1. Which parts of BiaPy would make good ops?

> Read AGENTS.md and the README in biapy-ops, then BiaPy's source
> (https://github.com/BiaPyX/BiaPy). List the functions that would make good
> ops: each one takes images and a few parameters a user would set, returns
> an image, labels or a table, and is useful on its own outside a full BiaPy
> workflow. For each, say what its op's signature would be, what in BiaPy
> would have to change (if anything) to wrap it cleanly, and whether
> scikit-ops (https://github.com/apposed/scikit-ops) already has something
> equivalent. Don't write code yet.

## 2. Add one op

> Read AGENTS.md. Add an op for BiaPy's `<module.function>` to biapy-ops, as
> `biapy_ops.<namespace>:<op_name>`, following
> `src/biapy_ops/segment/watershed_by_channels.py`. Expose only what a user
> would set: `<the parameters you want>`. Add it to `tests/test_ops.py` and a
> test on a small synthetic image to `tests/test_with_oprunner.py`, and run
> `uv run pytest` and `uv run pytest -m env`.

## 3. Rebuild this from scratch, your way

> Make a package of ops for BiaPy, modeled on biapy-ops
> (`<path or URL>`) -- read its AGENTS.md first, including "Things that will
> bite". The ops are: `<your list>`. Use one environment, `envs/biapy`,
> with BiaPy from PyPI. Keep each op a thin wrapper that changes nothing
> about BiaPy, and write down anything in BiaPy that made an op awkward. Add
> tests that check every op is a valid spec, and tests that run each op in
> its environment.

## 4. Put the ops inside BiaPy itself

A separate package is one choice. The ops could live in BiaPy instead, so
they are released and versioned with it.

> Read biapy-ops' AGENTS.md. Move its ops into BiaPy as a subpackage,
> `biapy.ops`, registered with an `opspec.collections` entry point in
> BiaPy's pyproject.toml. opspec should be an optional dependency
> (`pip install biapy[ops]`), and nothing in BiaPy should import `biapy.ops`
> unless asked. Keep the environment recipe (`envs/biapy/pixi.toml`) with the
> ops, and make it install BiaPy itself rather than biapy-ops.

## 5. Make BiaPy easier to run as an op

These change BiaPy, not biapy-ops; each removes a workaround here. See the
README's "Notes for BiaPy".

> In BiaPy, make `BiaPy(...)` leave `sys.stdout`, `sys.stderr` and
> `builtins.print` as it found them once a call returns (or never replace
> them process-wide), so BiaPy can run inside a host that talks over stdout.
> Then remove `_streams_kept` from biapy-ops' `predict.py` and check that
> `uv run pytest -m env` still passes.

> In BiaPy, add a public way to get the network's raw output from
> `predict()` -- e.g. `predict(image, stage="raw")` -- so biapy-ops'
> `predict.bmz(output="raw")` doesn't read the private
> `workflow._predictions`.

> In BiaPy, make `biapy.data.post_processing` import torch, cv2, zarr, h5py
> and matplotlib only inside the functions that need them, so the
> post-processing functions can run in a small environment without PyTorch.

## 6. A Fiji script

> Read AGENTS.md's Fiji section and the two scripts in
> `fiji/script_templates/biapy-ops/`. Write a Fiji Jython script that
> `<what it should do>`, calling ops as `skop.biapy_ops.<namespace>.<op>`.
> Use script parameters (`#@`) for everything a user would set, show the
> result as a new image, and put it in `fiji/script_templates/biapy-ops/`.
