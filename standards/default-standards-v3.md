---
name: Ezo Senior Code Review Protocol
version: "3.0"
description: Precise coding standards for financial systems
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

<section name="phase-1">
## Phase 1: Structural Integrity

If the structure is wrong, the code does not matter.

### 1.1 Flat Folder Hierarchy

**Rule:** Maximum 2 levels of nesting under a domain folder.

```
✅ ops/schemas/
✅ ops/types/
✅ ops/utils/
❌ ops/shared/schemas/
❌ ops/shared/utils/
```

**Rationale:** Deep nesting creates discovery friction. Each additional level is a cognitive tax.

### 1.2 Canonical Location Principle

**Rule:** Each concern has exactly one home. If two folders serve the same purpose, merge them.

**Check:** Are constants duplicated across `apps/*`, `api/*`, and shared packages? If yes, consolidate.

```
❌ apps/web/constants/currencies.ts
❌ api/constants/currencies.ts
✅ @ezo/constants/currencies.ts (single source)
```

### 1.3 No Re-export Chains

**Rule:** Never re-export from an external package through a local index.

```typescript
// ❌ @ezo/constants/index.ts
export * from './currencies'

// ❌ apps/web/lib/constants.ts
export * from '@ezo/constants'

// ✅ Import directly
import { USD, EUR } from '@ezo/constants/currencies'
```

**Rationale:** Re-export chains hide the true source, making refactoring hazardous.
</section>

<section name="phase-2">
## Phase 2: Boundary Discipline

### 2.1 Single Validation Location

**Rule:** Each concern validates in exactly one place.

| Concern | Validator | Location |
|---------|-----------|----------|
| Input shape | Zod schema | API entry point |
| Financial capacity | String length check | Before BigInt conversion |
| Business rules | Domain logic | Service layer |
| Referential integrity | Database | Foreign key constraints |

**Rationale:** Duplicated validation creates drift. Trust the layer that owns the concern.

### 2.2 No Interior Guard Spam

**Rule:** If the database enforces `NOT NULL`, do not write `value ?? fallback` in application code.

```typescript
// ❌ DB has NOT NULL, but code guards anyway
const name = user.name ?? 'Unknown'

// ✅ Trust the constraint
const name = user.name
```

**Exception:** Only guard when the source is genuinely unreliable (external APIs, user input before validation).

### 2.3 Storage-UI Separation

**Rule:** Constants describing database implementation must not appear in UI code.

```typescript
// ❌ Leaks DB detail to frontend
export const MAX_DECIMAL_SCALE = 18
// Frontend uses this for display

// ✅ Separate concerns
// Backend: db-config.ts
const DECIMAL_PRECISION = 18

// Frontend: display-config.ts
const DISPLAY_DECIMALS = 4
```
</section>

<section name="phase-3">
## Phase 3: Recipe Readability

Code must read top-to-bottom like a cooking recipe. If understanding execution requires jumping between files, it fails review.

### 3.1 Linear Execution Principle

**Rule:** Each function tells a complete story in sequence.

```typescript
// ✅ Recipe pattern - read top to bottom
async function processPayment(input: PaymentInput) {
  // 1. Validate capacity (string length before BigInt)
  if (input.amount.split('.')[0].length > MAX_AMOUNT_DIGITS) {
    throw new TRPCError({ code: 'BAD_REQUEST', message: 'Amount exceeds capacity' })
  }

  // 2. Convert to safe numeric type
  const amount = BigInt(input.amount)
  const fee = BigInt(input.fee)

  // 3. Business invariant
  if (amount <= fee) {
    throw new TRPCError({ code: 'BAD_REQUEST', message: 'Fee exceeds amount' })
  }

  // 4. Execute
  const net = amount - fee
  await db.insert(payments).values({ amount: net.toString() })
}
```

### 3.2 Indirection Detection

**Smells that fail review:**

| Pattern | Problem |
|---------|---------|
| Helper used once | Inlines are clearer |
| "Guard" classes | Adds cognitive load without value |
| Wrapper for native API | Hides obvious behavior |

```typescript
// ❌ Helper used once
const isValidAmount = (s: string) => s.split('.')[0].length <= 15
if (isValidAmount(input.amount)) { ... }

// ✅ Inline is self-documenting
if (input.amount.split('.')[0].length <= MAX_AMOUNT_DIGITS) { ... }
```

### 3.3 Drizzle ORM Clarity

**Rule:** Database queries must be direct and readable.

```typescript
// ❌ Callback pattern obscures the query
await db.select().from(users).where((t, { eq }) => eq(t.id, input.id))

// ✅ Explicit where clause
await db.select().from(users).where(eq(users.id, input.id))
```
</section>

<section name="phase-4">
## Phase 4: Financial Integrity

**Policy: Zero-Tolerance. Violation = Automatic REJECT.**

### 4.1 BigInt-Only Math

**Rule:** All financial calculations use `BigInt`. No exceptions.

```typescript
// ❌ Precision loss
const total = parseFloat(a) + parseFloat(b)

// ✅ Exact arithmetic
const total = BigInt(a) + BigInt(b)
```

### 4.2 String Transport

**Rule:** Money values are strings at every API boundary.

```typescript
// ❌ Number in transport
interface PaymentResponse { amount: number }

// ✅ String transport
interface PaymentResponse { amount: string }
```

**Exception:** Number conversion is allowed only at the final call to a 3rd-party SDK that requires it.

### 4.3 No Logic Wrappers

**Rule:** Use native operators directly. Do not abstract `BigInt` comparison.

```typescript
// ❌ Unnecessary wrapper
if (compareNumericStrings(a, b) > 0) { ... }

// ✅ Native is clearer
if (BigInt(a) > BigInt(b)) { ... }
```
</section>

<section name="phase-5">
## Phase 5: Time Authority

### 5.1 Frontend Owns Timezone

**Rule:** Backend receives ISO strings. Backend does not interpret timezones.

```typescript
// ✅ Frontend sends timezone-aware boundaries
POST /api/transactions { startDate: '2024-01-01T05:00:00Z', endDate: '2024-01-02T04:59:59Z' }

// ❌ Backend calculates day boundaries
const startOfDay = new Date().setHours(0, 0, 0, 0)
```

### 5.2 Dependency Hygiene

**Rule:** Backend must not import `luxon` or `date-fns`. Use native `Date` and `Intl`.

**Rationale:** Timezone logic belongs in the presentation layer. Backend stores and retrieves.

### 5.3 Updated At Handling

**Rule:** Database manages `updatedAt`. Do not send in mutation payloads.

```typescript
// ❌ Manual update
await db.update(users).set({ ...input, updatedAt: new Date() })

// ✅ Let DB handle it
await db.update(users).set(input) // DB trigger updates updatedAt
```
</section>

<section name="phase-6">
## Phase 6: API Contracts

### 6.1 Data Minimalism

**Rule:** Return primitive fields only. UI composes derived values.

```typescript
// ❌ Computed in API
return { fullName: `${user.firstName} ${user.lastName}` }

// ✅ Primitives only
return { firstName: user.firstName, lastName: user.lastName }
```

### 6.2 Status Over Boolean

**Rule:** HTTP status and response presence indicate success. Remove `success: true`.

```typescript
// ❌ Redundant
return { success: true, data: user }

// ✅ Implicit success
return user
```

### 6.3 Barrel Hygiene

**Rule:** `index.ts` exports its own directory only.

```typescript
// ❌ Re-exports external package
export * from 'lodash'

// ✅ Exports local modules only
export * from './user'
export * from './payment'
```
</section>

<section name="phase-7">
## Phase 7: Utility Discipline

### 7.1 The Inlining Threshold

**Rule:** Delete utilities that meet ALL of:
1. Fewer than 5 lines of logic
2. Used in fewer than 3 locations
3. Wraps native functionality

**Action:** Inline it.

```typescript
// ❌ 2-line helper, used once
const formatDate = (d: Date) => d.toISOString().split('T')[0]
const today = formatDate(new Date())

// ✅ Inline when trivial
const today = new Date().toISOString().split('T')[0]
```

### 7.2 Cognitive Load Test

**Rule:** If an abstraction requires reading its implementation to understand usage, delete it.

**Good abstraction:** `debounce(fn, 500)` — behavior is clear from signature.

**Bad abstraction:** `withRetry(fn, { max: 3, delay: 'exponential' })` — requires reading implementation.
</section>

<section name="checklist">
## Pre-Submit Checklist

Reviewers check these in order:

1. **Structure:** Is the folder hierarchy flat? Is each concern in one place?
2. **Boundaries:** Is validation at the correct layer? Are DB constraints trusted?
3. **Readability:** Does the function read top-to-bottom without jumps?
4. **Financial:** Is all math `BigInt`? Are values strings at boundaries?
5. **Time:** Does backend avoid timezone logic? Is `updatedAt` handled by DB?
6. **API:** Are responses minimal? Is `success: true` removed?
7. **Utilities:** Is every utility above the inlining threshold?

## Testing Policy

We prioritize architectural correctness and database constraints over unit test coverage.

**When tests ARE required:**
- Complex state machines
- Multi-step financial calculations
- Integration points with external systems

**When tests are NOT required:**
- Code following the Recipe pattern (Phase 3)
- Validation delegated to schemas or DB constraints
- CRUD operations

Reviewers: Do not flag missing test coverage unless a standards section explicitly requires tests.
</section>