# Wenu and Wenu3D Development Cheat Sheet

**Last updated:** 2026-07-30

This sheet records the development cycle used for Wenu and Wenu3D, including
the transfer of milestone patches from ChatGPT to a Mac.

## 1. Development principles

1. The checked-out Git repository is the source of truth.
2. Read the repository's assistant/developer instructions and roadmap before
   changing code.
3. Inspect the active implementation before proposing a modification.
4. Work in small, named milestone increments.
5. Keep the package working after every major milestone.
6. Run focused tests, the full suite, and the canonical visual example.
7. Commit and push only after Fernando confirms the tests and visual result.
8. Keep `main` stable; continue milestone work on the active feature branch
   until it is ready to merge.
9. Do not mix unrelated cleanup into a milestone.
10. Update architecture documentation at milestone boundaries.

## 2. Start a development session

Move to the repository:

```bash
cd /path/to/wenu
```

or:

```bash
cd /path/to/wenu3d
```

Confirm the repository state:

```bash
git status
git branch --show-current
git log -1 --oneline
```

The normal starting state is a clean working tree on the intended branch.

Update repository references when appropriate:

```bash
git fetch origin
git status
```

Do not switch branches, pull, merge, or reset merely because a remote update
exists. First verify that the action belongs to the current milestone.

## 3. Install the package for development

Activate the correct Conda environment first, then:

```bash
python -m pip install -e .
```

Confirm package imports:

```bash
python -c "import wenu"
```

or:

```bash
python -c "import pkgutil, wenu3d; [__import__(m.name) for m in pkgutil.iter_modules(wenu3d.__path__, 'wenu3d.')]"
```

## 4. Patch ZIP format

Every downloadable milestone is delivered as:

```text
<unique-milestone-name>.zip
└── <unique-milestone-name>/
    ├── README.md
    └── <unique-milestone-name>.patch
```

Rules:

- use a unique ZIP and directory name for every milestone;
- include a README with the exact base commit, scope, verification, and commit
  commands;
- keep the ZIP outside the Git repository;
- do not commit the ZIP, extracted directory, patch, or generated images.

## 5. Transfer a patch ZIP to the Mac

1. Download the ZIP link from the chat.
2. Safari or Finder normally expands it into a same-named directory under
   `Downloads`. If the ZIP remains compressed, open it once in Finder.
3. In Terminal, remain at the root of the target repository.
4. Refer to the patch with `$HOME`, not a hard-coded `/Users/...` path.

Example:

```bash
git status
git branch --show-current

git apply --check \
  "$HOME/Downloads/<zip-directory>/<patch-file>.patch"

git apply \
  "$HOME/Downloads/<zip-directory>/<patch-file>.patch"
```

Always run `git apply --check` first. An empty response means the check
succeeded.

Do not apply the patch if:

- the working tree is unexpectedly dirty;
- the branch is wrong;
- the patch check reports that it does not apply;
- the README's base commit does not match the intended repository state.

## 6. Inspect an applied patch

```bash
git status
git diff --stat
git diff
git diff --check
```

For a large diff, inspect named files individually:

```bash
git diff -- src/package/module.py
git diff -- tests/test_module.py
```

`git diff --check` should produce no output.

## 7. Python verification

Compile changed modules:

```bash
python -m py_compile src/package/module.py
```

Run focused tests:

```bash
python -m pytest -q tests/test_relevant_feature.py
```

Run the complete suite:

```bash
python -m pytest -q
```

Useful verbose forms:

```bash
python -m pytest -v tests/test_relevant_feature.py
python -m pytest -x
```

- `-v` shows individual test names.
- `-x` stops after the first failure.

## 8. Canonical visual checks

Wenu3D:

```bash
python examples/la_ligua_interactive_grids.py
```

Check:

- the window opens and closes normally;
- expected grids, annotations, Earth, observer, and shell are present;
- controls respond;
- there are no new overlaps or obvious visual regressions;
- saved output is created when expected.

For Wenu, run the current canonical planisphere or chart example specified by
its repository documentation. Do not substitute a historical notebook without
first confirming that it remains supported.

Visual refinement can be deferred when the milestone concerns architecture,
provided the illustration remains scientifically correct and operational.

## 9. Stage changes explicitly

Prefer explicit paths:

```bash
git add src/package/module.py \
  tests/test_module.py \
  docs/developer/current_architecture.md
```

Inspect what will be committed:

```bash
git status
git diff --cached --stat
git diff --cached
git diff --cached --check
```

Avoid `git add .` when unrelated files may exist.

## 10. Commit and push

Use one focused milestone message:

```bash
git commit -m "M7.1: describe the increment"
git push
git status
```

The final `git status` should report:

```text
nothing to commit, working tree clean
```

Record the resulting commit SHA in the development handoff.

## 11. Recover before committing

If a patch was applied but should be discarded, first inspect its exact scope:

```bash
git status
git diff --stat
```

Restore named tracked files only:

```bash
git restore src/package/module.py \
  tests/test_existing_module.py
```

Remove only the exact new file created by the failed patch:

```bash
rm -f tests/test_new_feature.py
```

Then verify:

```bash
git status
python -m pytest -q
```

Never use broad destructive commands such as `git reset --hard` or recursive
deletion for ordinary patch recovery.

If changes were staged but not committed:

```bash
git restore --staged path/to/file
```

Then decide whether to keep or restore the working-tree version.

## 12. When `git apply --check` fails

Do not force the patch.

Collect:

```bash
git status
git branch --show-current
git log -1 --oneline
```

Report the exact error and current commit. A replacement patch should be
generated from the actual current branch and commit.

Common causes:

- the patch was based on an earlier commit;
- one of its files already changed;
- the wrong repository or branch is active;
- an earlier partial application left local changes.

## 13. Milestone completion checklist

```text
[ ] correct repository and branch
[ ] expected base commit
[ ] working tree clean before applying
[ ] patch check succeeds
[ ] patch applies
[ ] Python compilation succeeds
[ ] git diff --check succeeds
[ ] focused tests pass
[ ] full test suite passes
[ ] canonical visual example passes
[ ] output files were not staged
[ ] only intended files are staged
[ ] staged diff check succeeds
[ ] focused commit created
[ ] commit pushed
[ ] final working tree clean
[ ] architecture documentation updated at major milestone boundary
```

## 14. Current Wenu3D handoff

At the end of 2026-07-30:

- repository: `fselman/wenu3d`;
- branch: `feature/interactive-grid-controls`;
- M6 completion commit: `8617d37`;
- M6 tests and canonical visual example passed;
- working tree was clean and synchronized with the remote;
- next milestone: M7, celestial shell as an explicit scene object or layer.

M7 must move shell mesh ownership, material refresh, presence, style use, and
camera-observer lifecycle out of `CelestialScene` while preserving appearance
and keeping the product operational after each increment.

## 15. Development handoff format

At the end of a session, record:

```text
Repository:
Branch:
Last pushed commit:
Completed milestone:
Tests:
Visual verification:
Working-tree status:
Known limitations:
Next milestone:
Patch ZIP convention:
```

This short record, together with the repository and roadmap, is sufficient to
resume work without reconstructing files from conversation memory.
