# Lessons

- Pattern: Package-level eager imports can make core modules fail when optional/runtime web dependencies are not installed.
  - Preventive rule: Keep package `__init__` lightweight and lazily import web app factories so command/config/model services remain independently testable.
- Pattern: CI/container dependency installation may be blocked even when network appears enabled.
  - Preventive rule: Separate core tests from runtime integration tests with explicit skips for missing optional dependencies, and document the exact environment limitation.
