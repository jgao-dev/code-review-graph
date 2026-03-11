---
name: Ezo Senior Code Review Protocol
version: "2.3"
description: Comprehensive coding standards for financial systems
author: John Gao
company: Ezo
---

# Code Review Standards

Use `get_review_standards_tool(section_name="<phase>")` to load specific phases.

## Installation

### Install as Claude Code Plugin

```bash
claude plugin marketplace add ezo-ai/code-review-graph
claude plugin install code-review-graph@code-review-graph
```

### Install via pip

```bash
pip install code-review-graph
code-review-graph install
```

Restart Claude Code after either method. Requires Python 3.10+ and [uv](https://docs.astral.sh/uv/).

### Custom Standards

To use your own standards, create `.code-review-standards.md` in your repo root:

```markdown
<section name="my-phase">
## My Custom Phase
Your coding standards here...
</section>
```

The plugin will auto-discover and use your standards instead of the defaults.

---

<section name="phase-0">
## Phase 0: Structural Integrity & Anti-Bloat

If the structure is wrong, the code does not matter.

### Folder Flattening Rule
No unnecessary nesting. Avoid `ops/shared/*`.

✅ Correct: `ops/schemas`, `ops/types`, `ops/utils`

The "One Location" Check: If two folders share a name (e.g., schemas) or constants are duplicated across layers, merge them. Exactly one canonical location per concern.

### Constant Boundary Check [CRITICAL]
Constants must respect layer boundaries.

- Frontend: `apps/*`
- Backend: `api/*`
- Truly Shared: `@ezo/constants`

No Re-export Chains: Never `export * from '@ezo/constants'` inside a local index. Import directly from the source.

### Intent vs Value Rule
Storage details must not leak into the UI.

The Rule: If a constant describes a DB implementation detail (e.g., `DECIMAL(27,18)`), it must not cross the boundary.

✅ Pattern: Storage uses `DB_SCALE = 18`. UI uses `DISPLAY_PRECISION = 4`.
</section>

<section name="phase-0.5">
## Phase 0.5: The Anti-Defensive Bloat Rule

Validation belongs at the boundary, not the middle.

### Boundary Validation Principle
Trust the Schema, the DB, and the Types. Heavy validation happens only at:
- API Input (Zod)
- DB Constraints (Unique/Not Null)
- Output Serialization

Stop the Spam: If the DB says NOT NULL, do not code `value ?? fallback`. No mid-function guard spam.

### Single Validation Location

| Concern | Location |
|---------|----------|
| Input Shape | Zod Schema |
| Financial Capacity | String length check (pre-BigInt) |
| Business Logic | API Layer |
| Referential Integrity | Database Engine |
</section>

<section name="phase-0.6">
## Phase 0.6: The Recipe Readability Rule

Code must read top-to-bottom like a cooking recipe.

If understanding execution requires opening multiple files, it fails review.

Smells of Indirection:
- Helper functions used once
- "Guard" classes
- Wrapper utilities for native logic

Example of "Recipe" Logic:
```typescript
// 1. Validate Capacity
if (input.amount.split('.')[0].length > MAX_AMOUNT_INTEGER_DIGITS) {
  throw new TRPCError({ code: 'BAD_REQUEST' })
}

// 2. Convert & Execute
const amount = BigInt(input.amount)
const fee = BigInt(input.fee)

if (amount <= fee) throw new TRPCError({ code: 'BAD_REQUEST' })

const net = amount - fee // Linear. Deterministic. Auditable.
```

### Drizzle ORM Clarity
Database queries must be direct. No clever callbacks or destructuring.

❌ Forbidden: `where: (tbl, { eq }) => eq(tbl.id, input.id)`

✅ Correct: `where: eq(opsIdentities.id, input.id)`
</section>

<section name="phase-1">
## Phase 1: Financial Integrity

**Policy: Zero-Tolerance. Violation = Automatic REJECT.**

### The BigInt Rule
- All math uses BigInt. No `parseFloat` or `Number()`.
- Transport/Storage: Money is always a String. Never transport numbers via API.
- The Boundary Exception: Number conversion is only allowed at the final outbound call to a 3rd-party SDK.

### No Logic Wrappers
Do not use `compareNumericStrings(a, b)`. Use `if (BigInt(a) > BigInt(b))`.
</section>

<section name="phase-2">
## Phase 2: Time & Frontend Authority

The backend is timezone-agnostic.

### Direction of Knowledge
- The Frontend calculates day boundaries (ET/UTC).
- The Backend receives ISO strings.

### Dependency Hygiene
Backend must not import luxon or date-fns. Use native Date and Intl.

### Updated At
Let the DB handle it. Do not manually send `updatedAt` in mutation payloads.
</section>

<section name="phase-3">
## Phase 3: API Contracts & Transport

### Data Minimalism
Return raw data only. No `fullName: "John Doe"` (UI composes this).

### Status Codes over Booleans
Remove `success: true`. The HTTP 200/tRPC response handles this.

### Barrel Hygiene
An `index.ts` only exports its own directory. Never re-export external packages.
</section>

<section name="phase-4">
## Phase 4: The Utility Purge

### The 5-Line Rule
If a function is < 5 lines, used < 3 times, or wraps native logic: Delete it. Inline it.

### Indirection Kill Switch
If an abstraction increases cognitive load without reducing complexity, kill it.
</section>

<section name="summary">
## Pre-Submit Mental Checklist

- [ ] Is this a "Recipe" (Top-to-bottom) or a "Maze" (Jumping files)?
- [ ] Is financial math strictly BigInt?
- [ ] Did I avoid "Defensive Bloat" (trusting the DB/Schema)?
- [ ] Is the folder structure flat?
- [ ] Did I remove `success: true` and unnecessary 5-line helpers?
- [ ] Is `updatedAt` handled by MySQL?

### Testing Policy
We prioritize architectural correctness and DB constraints over unit test coverage. Reviewers: Do not flag a lack of tests if the logic follows the "Recipe" rule and validation is handled at the boundary.

### Agent Review Guidance
If the codebase lacks tests, do not suggest adding them. Focus on standards compliance and logic correctness. Only mention testing if explicitly required by a standards section. Do not flag missing test coverage as an issue.
</section>