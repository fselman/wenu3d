# AI Assistant Instructions for Wenu3D

This document defines the expected behavior of AI assistants contributing to the Wenu3D project. Its goal is to preserve architectural consistency, avoid accidental regressions, and ensure that all changes are incremental, reviewable, and reproducible.

---

# Guiding Principles

Wenu3D is **not** an interactive planetarium.

Its primary goal is to provide a reusable library for creating **high-quality 3D scientific illustrations** of astronomical concepts for teaching, publications, and outreach.

The software should prioritize:

- correctness
- simplicity
- maintainability
- reproducibility
- publication-quality rendering

over maximum flexibility or real-time performance.

---

# Source of Truth

**The Git repository is always the source of truth.**

Never reconstruct files from memory or previous conversations.

Before proposing any modification:

1. Inspect the current implementation.
2. Base every proposal on the current code.
3. Modify only what is necessary.

Previous conversations are useful only for understanding design intent.

---

# Development Workflow

Work incrementally.

Each change should:

- compile
- run
- leave the project in a usable state

Prefer several small commits over one large commit.

Never perform unrelated refactoring while implementing a requested feature.

---

# Architectural Authority

The project roadmap is authoritative.

Before introducing new abstractions or changing existing ones:

- verify that they are consistent with the roadmap
- preserve architectural coherence

If a proposal intentionally departs from the roadmap, explain:

- why the change is beneficial
- what alternatives were considered
- why the existing design is insufficient

before modifying any code.

---

# Working with Git

Always assume development occurs on the active Git branch.

Do not assume the branch name.

Do not assume repository contents.

Before modifying files:

- inspect the current implementation
- work against the current branch

Never recreate files from memory.

---

# Scope of Changes

Modify only files required for the requested task.

Avoid touching unrelated files.

Do not perform opportunistic cleanup.

Do not reformat unrelated code.

Preserve the project's existing coding style.

---

# Temporary Files

Never create temporary files inside the repository unless explicitly requested.

Examples include:

- backup directories
- generated ZIP files
- temporary documentation
- intermediate scripts
- exported images

If temporary files are needed, place them outside the repository whenever possible.

---

# Generated Files

Do not automatically generate:

- README updates
- documentation
- example notebooks
- screenshots
- test data

unless explicitly requested.

---

# Backward Compatibility

Prefer preserving existing APIs.

When changing an API:

- explain the reason
- minimize disruption
- migrate examples if necessary

---

# Rendering Philosophy

Rendering should emphasize:

- visual clarity
- scientific accuracy
- clean aesthetics

rather than visual effects.

When multiple rendering solutions exist, prefer the simplest solution that achieves the desired appearance.

Avoid unnecessary complexity.

---

# User Interface

Interactive controls should:

- be consistent
- be organized logically
- scale as additional scene objects are added

Avoid one-off controls.

Prefer reusable control abstractions.

---

# Object Model

Favor explicit scene objects.

The architecture should evolve toward:

```
Scene
    Layer
        SceneObject
```

where every drawable object exposes a consistent interface.

Avoid special-case handling whenever possible.

---

# Scientific Accuracy

Astronomical correctness always takes precedence over graphical appearance.

Visual simplifications are acceptable only when they do not introduce conceptual errors.

---

# Communication Style

When proposing architectural changes:

1. explain the reasoning
2. explain the tradeoffs
3. describe the expected benefits

before presenting code.

---

# Preferred Development Style

Prefer:

- small incremental patches
- reviewable changes
- explicit reasoning
- stable interfaces

Avoid:

- replacing entire files unnecessarily
- speculative refactoring
- introducing abstractions without clear benefit

---

# If Unsure

If the current implementation does not clearly support the requested change:

- inspect the relevant files
- ask for clarification if needed

Never guess.

The repository is always the authoritative reference.
