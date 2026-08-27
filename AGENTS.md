# Agent operating contract

Zanshin Proof is an accountability system. Work on it must preserve that principle.

- Treat the requested scope and acceptance criteria as a contract.
- Keep policy evaluation deterministic. Language models may produce evidence, but they do not decide whether deterministic checks pass.
- Never weaken, remove, or convert a required check to optional solely to make a gate pass.
- Preserve user work and avoid destructive Git operations.
- Separate observed evidence from inference and label uncertainty.
- Never invent provenance identifiers or timestamps to satisfy a schema.
- Treat public schemas as compatibility contracts and version breaking changes.
- Test public behavior and failure modes before claiming completion.
- Keep changes small enough to review and explain outcomes in plain language.
- Human approval is a distinct future control; an agent must never approve its own work.
