# Contributing to knob-param

See **[AGENTS.md](AGENTS.md)** — it applies to humans and cloud agents alike. Short version:

1. Branch off `param-dev` (never `main`): `sub/<sub>-<topic>` or `asm/<topic>`.
2. Touch only `cad/knob-param/knobparam/<your sub>/` (assembly agent: `assembly/`, `common/`, `cad/assemblies/`).
3. `python build.py --contract` must print `contract: OK`; `python build.py --sub <sub>` must not add FAILs.
4. Open a PR into `param-dev` with the `--sub` summary. The assembly agent merges, renders and reports.
