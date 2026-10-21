# /research — Research & best practices

Gather information, explore options, recommend an approach. Step 1 of the
embedeval 5-stage workflow. Informs `/myplan` — does **not** create any file.

## Communication

- Direct, evidence-based, no preamble.
- When reasoning is flawed, say so with specific evidence.
- Don't fold on pushback without new evidence.
- Lead with concerns before agreement.

## Usage

```
/research <topic or task>
```

Use Opus with ultrathink for thorough analysis.

## Context

- Repo root: `/home/noel/embedeval`
- Published docs: `docs/*.md` (METHODOLOGY, BENCHMARK-*, LLM-EMBEDDED-*)
- Existing plans: `plans/PLAN-*.md`
- Prior corrections: `CLAUDE.md` → "Learned Corrections"
- Domain references:
  - `docs/LLM-EMBEDDED-FAILURE-FACTORS.md` — 42 factors, 6 categories
  - `docs/LLM-EMBEDDED-DEVELOPMENT-GUIDE.md` — end-to-end workflow
  - `docs/LLM-EMBEDDED-CONSIDERATIONS.md` — production failure patterns

## Steps

1. **Codebase scan** — use `Agent(subagent_type="Explore")` for broad
   exploration, or Grep/Glob directly for narrower searches. Inspect
   `src/embedeval/`, `cases/`, relevant tests.

2. **Prior embedeval work** — grep `plans/PLAN-*.md` and CLAUDE.md corrections
   for related topics. Read every hit that looks relevant.

3. **External research** — WebSearch for best practices, Context7 MCP for
   official library docs. Cite sources.

4. **Synthesize** — identify 2–3 approaches with pros/cons, complexity, risk,
   estimated effort.

## Output (screen only)

```
## Research: <topic>

### Problem
<what, why, constraints, success criteria>

### Approaches
#### Option A (recommended): <name>
- Pros / Cons / Complexity / Risk / Effort

#### Option B: <name>
- Pros / Cons / Complexity / Risk / Effort

### Prior embedeval work
<PLAN-*.md hits or CLAUDE.md corrections worth reusing/avoiding>

### External references
<web / Context7 / docs with links>

### Pitfalls
1. <pitfall> — <how to avoid>

### Recommendation
Proceed with Option <X>. Rationale: <2–3 sentences>.

### Next step
`/myplan <suggested-task-slug>`
```

## Validation

Stop and ask user:
1. Does this address the need?
2. Any option worth exploring in more depth?
3. Ready for `/myplan`?

## Notes

- Research output is never written to disk. If a finding is worth preserving,
  it belongs in the PLAN document produced by `/myplan`, or (if a project-wide
  learning) appended to CLAUDE.md "Learned Corrections" by `/wrapup`.
