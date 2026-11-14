# Working on biapy-ops

Instructions for a coding agent (Claude Code, Codex, Copilot, ...) and for
people. `CLAUDE.md` only points here.

## What this is

An **example**: a few of [BiaPy](https://github.com/BiaPyX/BiaPy)'s functions
wrapped as *ops*, so one front end can run them -- napari, Fiji, a notebook --
each in its own Python environment. It exists to show BiaPy's developers what
that would take. It is not a port of BiaPy, and which parts of BiaPy (if any)
become ops is BiaPy's decision. `PROMPTS.md` has prompts for redoing or
extending it.

An op is a plain Python function with type hints, a docstring and
`@op(env=...)`, from [opspec](https://github.com/apposed/scikit-ops/tree/main/opspec).
The signature *is* the spec: a front end builds its dialog from it, and a
runner (scikit-ops' `oprunner`, or Fiji's fiji-skopkit) runs the function in
the environment named by `env`.

## Layout

```
pyproject.toml          the package; its opspec.collections entry point is
                        what makes it a collection front ends find
src/biapy_ops/          the ops: one module per op, grouped by namespace
  predict.py            predict.bmz -- any BioImage Model Zoo model / .pth
  segment/              segment.watershed_by_channels
envs/biapy/pixi.toml    the environment the ops run in (BiaPy + PyTorch)
envs/biapy/init.py      run once at worker start, on the main thread
tests/                  test_ops.py: specs only; test_with_oprunner.py: runs them
examples/               a notebook running both ops
fiji/                   Fiji scripts and the launcher that wires Fiji to here
```

Sibling checkouts are expected next to this one: `../scikit-ops` (opspec,
ophelper, oprunner, scikit-ops) and, for Fiji, `../fiji-skopkit`.
`../tnia-ops` is another collection made the same way.

## Making an op

Copy `src/biapy_ops/segment/watershed_by_channels.py`; it is the whole
pattern.

1. **Module and namespace.** `src/biapy_ops/<namespace>/<op>.py`, or
   `<namespace>.py` for a namespace of one. Re-export it from the package's
   `__init__.py`. The op is then `biapy_ops.<namespace>:<op>`; in Fiji
   scripts, `skop.biapy_ops.<namespace>.<op>`.
2. **The signature is the user interface.** Only parameters a user would
   set. BiaPy's `cfg`, `save_dir`, `verbose` and the like are fixed inside
   the op, not exposed.
   - Arrays: `Annotated[ImageOf[np.ndarray], Axes("z?", "y", "x", "c?")]`
     for an image, `LabelsOf[np.ndarray]` for labels. `?` marks an optional
     axis. Axes are numpy order.
   - Bounds: `Annotated[int, {"min": 0, "max": 100000}]`.
   - Choices: an `Enum`.
   - Lists a user types: a comma-separated `str` ("F,C"), parsed in the op.
3. **The docstring.** First line: what it does. `Args:` entries become
   tooltips; write them for a microscopist, not a programmer.
4. **Import BiaPy inside the function**, never at module level. The op is
   *declared* in the front end's process, which has only opspec and numpy;
   it *runs* in `envs/biapy`.
5. **Check inputs early, in plain words**, before BiaPy does something
   cryptic with them (see `_check` in `watershed_by_channels.py`).
6. **Add it to `tests/test_ops.py`'s list**, and a case to
   `tests/test_with_oprunner.py` that runs it on a small synthetic image.

## Running and testing

```sh
uv sync
uv run pytest            # every op is a valid spec; seconds, no environment
uv run pytest -m env     # runs the ops: builds envs/biapy the first time
```

The first `-m env` run builds the environment (several GB: PyTorch). It is
built once, as `biapy-ops--biapy` under Appose's directory
(`~/.local/share/appose`), and shared by napari, Fiji and notebooks.

## Things that will bite

All found the hard way; each is worked around in this repo. Don't remove a
workaround without reading why it is there.

- **The worker talks to its host over stdout.** Anything that replaces
  `sys.stdout`, `sys.stderr` or `builtins.print` for the process breaks it,
  and the symptom is a *hang*, not an error. BiaPy does all three when a
  `BiaPy(...)` is created. `predict.py` puts them back after each BiaPy call
  (`_streams_kept`); any new op that creates a `BiaPy` object must use it.
- **Windows: first load of a native library from an op's thread can
  deadlock.** Ops run on worker threads. `envs/biapy/init.py` imports torch,
  scipy and BiaPy on the main thread at start-up; a new op that needs another
  heavy native module should import it there too.
- **Don't add numpy (or anything with BLAS) to the conda dependencies** in
  `envs/biapy/pixi.toml`. Conda's MKL numpy next to PyPI's OpenBLAS wheels
  crashed Python on `import biapy` (Windows error 0xc06d007f). Everything but
  Python comes from PyPI.
- **UTF-8.** BiaPy prints characters Windows' default pipe encoding can't
  encode; the environment sets `PYTHONUTF8=1`.
- **Output axes.** An op can't yet declare its output's axes, so Fiji names
  them after the input's. `bmz(output="raw")` adds a channel axis, which
  `fiji/script_templates/biapy-ops/BiaPy_Nuclei_Watershed.py` renames itself.
- **Private BiaPy API.** `bmz(output="raw")` reads
  `workflow._predictions`. If BiaPy changes it, that is what breaks.

## Fiji

`fiji/start-fiji.bat C:\path\to\Fiji` starts a Fiji (with fiji-skopkit
installed) wired to these checkouts: it sets `SKOP_COLLECTIONS` and
`SKOP_CHECKOUT`, puts the scripts in `fiji/script_templates/biapy-ops/` in
Fiji's Plugins menu and the Script Editor's Templates, and starts Fiji. The
ops themselves need no script: each gets a menu command, `Plugins ▸
biapy-ops ▸ ...`.

In scripts an op is always called with the collection's name,
`skop.biapy_ops.predict.bmz(imp)`, never `skop.predict.bmz` -- so a script
says whose op it runs. Keep it that way in new scripts.

## Conventions

- BiaPy's behaviour is not changed by an op: thin wrappers only. Where BiaPy
  would need a change to make an op clean, write it down in the README's
  "Notes for BiaPy" instead of working around it silently.
- License MIT, as BiaPy's, so code can move between the two.
- Commit messages: a short imperative subject, then why.
