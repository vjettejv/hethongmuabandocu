# Migration evidence

Current setup and architecture are documented in the [root README](../../README.md), [development guide](../development.md), [architecture](../architecture.md), [API guide](../api.md), and [CI/CD guide](../ci-cd.md). A new developer does not need to follow the historical phase instructions to run the current stack.

This directory retains the Node → Python audit, implementation, parity, safety, and recovery evidence. Earlier commands, phase-specific images, Windows paths, Node fixture references, and counts describe the repository at that time. They are intentionally retained and do not identify current runtime dependencies.

- Phase 0–1: repository/contract audit and Python foundation.
- Phase 2–6: gateway and service migrations, including parity with the previous backend.
- [Phase 7 implementation](phase-7-implementation-report.md): full integration and controlled retirement.
- [Subsequent frontend audit](frontend-audit-report.md) and [moderation normalization](post-status-normalization.md): authorized follow-up changes.
- [Phase 8 report](phase-8-report.md): CI/CD configuration, final documentation, clean bootstrap, and current verification results.

Phase 7's 913-test total and 46-upload inventory are historical. Phase 8 starts from a fresh safety snapshot that includes the later user changes and 47 uploaded files. Do not restore old rows/files merely to make old counts match.
