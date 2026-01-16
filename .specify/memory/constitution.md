<!--
===============================================================================
SYNC IMPACT REPORT
===============================================================================
Version Change: N/A → 1.0.0 (Initial ratification)
Modified Principles: N/A (Initial creation)
Added Sections:
  - Core Principles (4 principles: Code Quality, Testing Standards, UX Consistency, Performance)
  - Quality Gates
  - Development Workflow
  - Governance
Removed Sections: N/A
Templates Requiring Updates:
  - .specify/templates/plan-template.md ✅ (Constitution Check section already exists)
  - .specify/templates/spec-template.md ✅ (Requirements section aligns with principles)
  - .specify/templates/tasks-template.md ✅ (Test-first approach already documented)
Follow-up TODOs: None
===============================================================================
-->

# BabelDOC Constitution

## Core Principles

### I. Code Quality First

All code contributions MUST meet the following non-negotiable standards:

- **Type Safety**: All public interfaces MUST have complete type annotations. Python code MUST pass `mypy --strict` or equivalent type checking without errors.
- **Linting Compliance**: Code MUST pass configured linters (`ruff`, `flake8`, or project-equivalent) with zero warnings. No `# noqa` exceptions without documented justification in the PR.
- **Documentation**: Public APIs MUST include docstrings with parameter descriptions, return types, and usage examples. Internal functions SHOULD have docstrings when behavior is non-obvious.
- **Single Responsibility**: Each module, class, and function MUST have a single, clear purpose. If a function exceeds 50 lines or a module exceeds 500 lines, it MUST be evaluated for decomposition.
- **Dependency Management**: New dependencies MUST be justified in the PR description. Prefer standard library solutions when performance and maintainability are equivalent.

**Rationale**: BabelDOC is designed to be embedded in other programs. Code quality directly impacts integration reliability and maintainability for downstream consumers.

### II. Testing Standards

Testing is MANDATORY for all functional changes:

- **Coverage Threshold**: New code MUST maintain or improve overall test coverage. Critical paths (PDF parsing, translation, rendering) MUST have >80% line coverage.
- **Test Categories**:
  - **Unit Tests**: Required for all services, models, and utility functions. MUST be isolated with mocked dependencies.
  - **Integration Tests**: Required for cross-module interactions, especially PDF parsing → translation → rendering pipeline.
  - **Contract Tests**: Required when modifying CLI arguments, Python API signatures, or output formats.
- **Test-First for Bug Fixes**: Bug fixes MUST include a failing test that reproduces the issue BEFORE the fix is implemented.
- **Regression Prevention**: Any bug that reaches production MUST result in a test case to prevent recurrence.
- **Test Naming**: Test functions MUST follow the pattern `test_<function>_<scenario>_<expected_outcome>` for clear failure diagnosis.

**Rationale**: The PDF translation pipeline has complex interdependencies. Comprehensive testing prevents regressions that degrade output quality.

### III. User Experience Consistency

All user-facing interfaces MUST provide a consistent, predictable experience:

- **CLI Behavior**:
  - All commands MUST support `--help` with clear descriptions and examples.
  - Error messages MUST be actionable, indicating what went wrong and how to fix it.
  - Exit codes MUST follow convention: 0 for success, non-zero for errors with distinct codes for different failure categories.
  - Progress reporting MUST be consistent across all long-running operations.
- **Output Consistency**:
  - PDF output quality MUST be visually consistent across translation runs with identical inputs.
  - Bilingual and monolingual outputs MUST have matching layout structure.
  - Watermark behavior MUST be predictable and match documented `--watermark-output-mode` options.
- **Configuration**:
  - CLI arguments and TOML config options MUST use consistent naming (kebab-case for CLI, snake_case for TOML where standard).
  - Default values MUST be documented and stable across minor versions.
- **Backward Compatibility**:
  - Existing CLI arguments MUST NOT change behavior without deprecation warnings for at least one minor version.
  - Breaking changes to output format MUST increment the MAJOR version per versioning policy.

**Rationale**: Users depend on predictable behavior for automation workflows. Inconsistencies erode trust and increase support burden.

### IV. Performance Requirements

Performance is a feature, not an afterthought:

- **Translation Throughput**:
  - Single-page translation MUST complete within 30 seconds for average academic papers (excluding LLM latency).
  - Batch processing MUST scale linearly with `--pool-max-workers` up to the specified limit.
- **Memory Efficiency**:
  - Memory usage MUST NOT exceed 2GB for documents under 100 pages.
  - Large document processing MUST use streaming/chunking to avoid memory exhaustion.
  - `--max-pages-per-part` MUST effectively bound memory usage for arbitrarily large documents.
- **Output Quality Metrics** (per project roadmap):
  - Layout error rate MUST be <1% for supported document types.
  - Content loss rate MUST be <1% for supported document types.
- **Performance Regression Prevention**:
  - Changes affecting PDF parsing or rendering MUST include benchmark comparisons.
  - Performance degradation >10% on standard benchmarks MUST be justified or rejected.
- **Startup Time**:
  - `babeldoc --help` MUST respond within 2 seconds.
  - `babeldoc --warmup` MUST complete asset verification within reasonable network conditions.

**Rationale**: BabelDOC processes academic documents where layout fidelity is critical. Performance constraints ensure the tool remains practical for large-scale document processing.

## Quality Gates

All pull requests MUST pass these gates before merge:

| Gate | Requirement | Enforcement |
|------|-------------|-------------|
| Type Check | `mypy` passes with zero errors | CI blocking |
| Lint | Configured linter passes with zero warnings | CI blocking |
| Unit Tests | All unit tests pass | CI blocking |
| Integration Tests | All integration tests pass | CI blocking |
| Coverage | Coverage does not decrease for modified files | CI advisory |
| Documentation | Public API changes include docstring updates | Reviewer check |
| Changelog | User-facing changes documented in appropriate location | Reviewer check |

## Development Workflow

### Code Review Requirements

- All changes MUST be reviewed by at least one maintainer before merge.
- Reviewers MUST verify compliance with Constitution principles.
- Self-merging is NOT permitted except for emergency hotfixes (which MUST be reviewed within 24 hours post-merge).

### Commit Standards

- Commit messages MUST follow conventional commits format: `type(scope): description`
- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `chore`
- Breaking changes MUST include `BREAKING CHANGE:` footer or `!` after type.

### Branch Strategy

- Feature branches MUST branch from and merge to `main`.
- Branch names SHOULD follow pattern: `type/brief-description` (e.g., `feat/table-support`, `fix/memory-leak`).

## Governance

### Amendment Process

1. Propose changes via pull request to this constitution file.
2. Changes require approval from at least two maintainers.
3. MAJOR version bump required for principle removals or fundamental redefinitions.
4. MINOR version bump for new principles or significant expansions.
5. PATCH version bump for clarifications, typos, or non-semantic refinements.

### Compliance Review

- Constitution compliance MUST be verified during code review.
- Violations MUST be documented and addressed before merge.
- Repeated violations MAY result in review of contributor access.

### Conflict Resolution

- When requirements conflict, prioritize in order: User Safety > Output Quality > Performance > Developer Convenience.
- Ambiguous cases SHOULD be raised as GitHub issues for maintainer discussion.

**Version**: 1.0.0 | **Ratified**: 2026-01-15 | **Last Amended**: 2026-01-15
