# Zanshin Proof

Evidence gates for agent-assisted machine learning changes.

Zanshin Proof evaluates observed facts and metrics against an explicit release policy. It gives
humans a compact evidence packet and gives CI a deterministic decision: pass, warn, or block.
Agents can help create code and collect evidence, but they do not approve their own work.

## First working slice

The repository currently supports:

- Versioned YAML release policies
- Required and optional checks
- Boolean assertions, regression tolerances, and numeric thresholds
- Machine-readable JSON reports
- CI-safe exit codes
- A recommendation-model example
- Draft 2020-12 JSON Schemas for policies, evidence, and reports
- Required provenance binding evidence to code, model, run, source, and collection time

## Try it

Requires [uv](https://docs.astral.sh/uv/) and Python 3.11 or newer.

```bash
uv sync --extra dev

uv run zanshin-proof evaluate \
  --policy examples/recommendation/policy.yml \
  --evidence examples/recommendation/evidence.json \
  --output proof-report.json
```

The example passes its required gates and surfaces catalog coverage as a warning. The command
returns `0` for `pass` or `warn`, `1` when a required check blocks release, and `2` for invalid
policy or evidence input.

Use `uv run pytest`, `uv run ruff check .`, and `uv build` for verification and packaging.

## Policy example

```yaml
version: 1
project: recommendation-ranking
checks:
  - id: auc-regression
    type: metric_regression
    candidate: metrics.candidate.auc
    baseline: metrics.baseline.auc
    tolerance: 0.005

  - id: calibration-error
    type: max_value
    path: metrics.candidate.ece
    maximum: 0.03
```

## Design principles

- Explicit intent before execution
- Deterministic gates over agent self-assessment
- Independent evidence with provenance
- Required failures cannot be explained away
- Human ownership of promotion and approval
- Durable architecture documentation instead of disposable agent notes

See [docs/architecture.md](docs/architecture.md) for system boundaries and planned integrations.

## Evidence provenance

Every evidence document must identify:

- The complete Git commit SHA evaluated
- The model name and version
- The originating run system and run ID
- The collector and collection timestamp
- At least one versioned source table, dataset, file, API, or manual input

This provenance is validated before any checks run and is copied unchanged into the report. The
schemas are packaged under `src/zanshin_proof/schemas/` and enforced at runtime.

## Near-term roadmap

1. Cryptographically signed evidence bundles
2. GitHub pull-request check integration
3. MLflow candidate-versus-baseline collector
4. Databricks job and release-pin verification
5. Human approval workflow and review UI
