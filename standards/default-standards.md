---
name: Ezo Code Review Standards
version: "4.0"
description: Simplified standards organized by domain
---

# Code Review Standards

Use `get_review_standards_tool(section_name="<section>")` to load specific sections.

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
<section name="principles">
## Principles
Your universal coding standards here...
</section>

<section name="frontend">
## Frontend
Your frontend-specific standards here...
</section>

<section name="backend">
## Backend
Your backend-specific standards here...
</section>
```

The plugin will auto-discover and use your standards instead of the defaults.

---

<section name="principles">
## Principles

These standards apply to all code regardless of domain.

### Structural Integrity

If the structure is wrong, the code does not matter.

#### Flat Folder Hierarchy

**Rule:** Maximum 2 levels of nesting under a domain folder.

```
✅ ops/schemas/
✅ ops/types/
✅ ops/utils/
❌ ops/shared/schemas/
❌ ops/shared/utils/
```

**Rationale:** Deep nesting creates discovery friction. Each additional level is a cognitive tax.

#### Canonical Location Principle

**Rule:** Each concern has exactly one home. If two folders serve the same purpose, merge them.

**Check:** Are constants duplicated across `apps/*`, `api/*`, and shared packages? If yes, consolidate.

```
❌ apps/web/constants/currencies.ts
❌ api/constants/currencies.ts
✅ @ezo/constants/currencies.ts (single source)
```

#### No Re-export Chains

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

#### No Re-exports in Module Files

**Rule:** Non-index files must not re-export. If a file defines its own exports, it cannot also re-export from elsewhere.

```typescript
// ❌ mock-deals.ts - module file with re-exports
import { OTC_DEAL_STATUSES } from '@ezo/constants/ops';
export { OTC_DEAL_STATUSES };  // Re-export hidden in module file
export const otcDealSchema = z.object({ ... });

// ✅ mock-deals.ts - clean module file
import { OTC_DEAL_STATUSES } from '@ezo/constants/ops';
// Use it internally, don't re-export
export const otcDealSchema = z.object({ status: OTC_DEAL_STATUSES[0] });

// ✅ index.ts - barrel file (only place re-exports belong)
export * from './mock-deals';
export * from './schemas';
```

**Rationale:** Re-exports in module files hide imports. Callers can't tell if an export comes from the file or is passed through. This makes refactoring hazardous—you might think you're editing the source when you're editing a passthrough.

**Detection:** If a file has BOTH `import` and `export` of the same identifier (including `export { X }` and `export type { X }`), it's a re-export. Flag it.

### Recipe Readability

Code must read top-to-bottom like a cooking recipe. If understanding execution requires jumping between files, it fails review.

#### Linear Execution Principle

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

#### Indirection Detection

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

#### Drizzle ORM Clarity

**Rule:** Database queries must be direct and readable.

```typescript
// ❌ Callback pattern obscures the query
await db.select().from(users).where((t, { eq }) => eq(t.id, input.id))

// ✅ Explicit where clause
await db.select().from(users).where(eq(users.id, input.id))
```

### Consistency First

**Rule:** Before creating any new utility, helper, or format function, search for existing patterns in the codebase.

```typescript
// ❌ Creating a new formatter without checking
const formatMoney = (amount: string) => {
  const num = parseFloat(amount)
  return `$${num.toFixed(2)}`
}

// ✅ Search first, find existing implementation
import { formatCurrency } from '@ezo/formatters'  // Already exists!
const display = formatCurrency(amount)
```

**Checklist before creating new utilities:**
1. Does a similar function already exist in the same file?
2. Does a similar function exist in nearby files in the same domain?
3. Does a shared utility package already provide this?
4. Can an existing utility be extended instead of creating a new one?

**Rationale:** Every new utility adds maintenance burden and creates inconsistency. The codebase should have one way to do each thing. Different implementations of the same logic drift apart.

### Utility Discipline

**Principle:** Readability and maintainability over everything. Delete unnecessary abstractions.

#### Inline Single-Use Functions

**Rule:** If a function is used only once, inline it.

```typescript
// ❌ Function declared but used once
const formatUserName = (user: User) => `${user.firstName} ${user.lastName}`
const displayName = formatUserName(currentUser)

// ✅ Inline it
const displayName = `${currentUser.firstName} ${currentUser.lastName}`
```

**Exception:** Extract to a function if the operation is complex and naming improves clarity.

#### Inline Short Functions

**Rule:** If a function is 1-2 lines, inline it regardless of reuse count.

```typescript
// ❌ 2-line helper, used twice
const formatDate = (d: Date) => d.toISOString().split('T')[0]
const today = formatDate(new Date())
const yesterday = formatDate(new Date(Date.now() - 86400000))

// ✅ Inline even if used multiple times
const today = new Date().toISOString().split('T')[0]
const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0]
```

**Rationale:** A 2-line function requires reading definition + call site. Inline code reads in one place.

#### Eliminate Single-Use Constants

**Rule:** If a constant is used once, evaluate if it's truly necessary.

```typescript
// ❌ Constant used once
const MAX_RETRIES = 3
await fetchWithRetry(url, { retries: MAX_RETRIES })

// ✅ Inline if the value is self-explanatory
await fetchWithRetry(url, { retries: 3 })

// ✅ Keep if the name adds semantic meaning
const MS_PER_DAY = 86400000
const weekAgo = Date.now() - (7 * MS_PER_DAY)  // 86400000 is not obvious
```

#### Cognitive Load Test

**Rule:** If an abstraction requires reading its implementation to understand usage, delete it.

**Good abstraction:** `debounce(fn, 500)` — behavior is clear from signature.

**Bad abstraction:** `withRetry(fn, { max: 3, delay: 'exponential' })` — requires reading implementation.

### Readability Over Performance

**Rule:** Prefer readable code over performant code when the trade-off is significant.

```typescript
// ❌ Optimized but hard to read
const result = arr.reduce((acc, x) => ({ ...acc, [x.id]: x }), {})

// ✅ Slightly slower but readable
const result: Record<string, Item> = {}
for (const x of arr) {
  result[x.id] = x
}
```

**Rule:** Only optimize when you have measured a real performance problem.

```typescript
// ❌ Premature optimization
const memo = useMemo(() => expensiveCalc(data), [data])

// ✅ Optimize only when needed
// Start with the simple version, add memoization if profiling shows it's slow
const result = expensiveCalc(data)
```

**Rationale:** Code is read 10x more than written. Optimization without measurement is guessing.

### Single Validation Location

**Rule:** Each concern validates in exactly one place.

| Concern | Validator | Location |
|---------|-----------|----------|
| Input shape | Zod schema | API entry point |
| Financial capacity | String length check | Before BigInt conversion |
| Business rules | Domain logic | Service layer |
| Referential integrity | Database | Foreign key constraints |

**Rationale:** Duplicated validation creates drift. Trust the layer that owns the concern.

#### No Defensive Bloat

**Rule:** Validate once at the edge. Never re-validate data that's already been validated.

```typescript
// ❌ Re-validating at every layer (defensive bloat)
const userRouter = router({
  update: protectedProcedure
    .input(userSchema)           // ✅ Validated here
    .mutation(async ({ input }) => {
      // ❌ Re-validating - bloat
      const parsed = userSchema.parse(input)
      return userService.update(parsed)
    })
})

// ❌ Service re-validates too
async function update(input: UserInput) {
  const parsed = userSchema.parse(input)  // ❌ Already validated at edge
  // ...
}

// ❌ Frontend re-validates after backend already validated
async function handleSubmit(formData: UserInput) {
  // Backend already validated via .input(schema)
  const validated = userSchema.parse(formData)  // ❌ Duplicate validation
  await api.updateUser(validated)
}

// ✅ Trust the edge validation
const userRouter = router({
  update: protectedProcedure
    .input(userSchema)           // Validated once here
    .mutation(async ({ input }) => {
      return userService.update(input)  // Use directly
    })
})

// ✅ Frontend trusts backend validation
async function handleSubmit(formData: UserInput) {
  await api.updateUser(formData)  // Backend validates, returns errors
}
```

**Rule:** Zod parsing is for validation, not transformation. If data is already typed, don't parse again.

```typescript
// ❌ Parsing already-validated data
async function processUser(user: User) {
  const parsed = userSchema.parse(user)  // ❌ User is already typed
}

// ✅ Use typed data directly
async function processUser(user: User) {
  // user is already validated and typed
}
```

### Barrel Hygiene

**Rule:** `index.ts` exports its own directory only.

```typescript
// ❌ Re-exports external package
export * from 'lodash'

// ✅ Exports local modules only
export * from './user'
export * from './payment'
```

### Pre-Submit Checklist

Reviewers check these in order:

1. **Structure:** Is the folder hierarchy flat? Is each concern in one place?
2. **Readability:** Does the function read top-to-bottom without jumps?
3. **Utilities:** Is every utility above the inlining threshold?
4. **Validation:** Is validation at the correct layer?

### TypeScript Type Safety

#### No Any Types

**Rule:** `any` is banned. Use `unknown` when type is uncertain.

```typescript
// ❌ any defeats TypeScript
function parse(data: any) { ... }

// ✅ unknown forces validation
function parse(data: unknown) {
  if (typeof data !== 'object' || data === null) return
  // ...
}
```

**Exception:** Migrating legacy code (add `// TODO: type this`).

#### No Type Assertions

**Rule:** Never use `as` to force types. If TypeScript disagrees, fix the type or add validation.

```typescript
// ❌ Lies to TypeScript
const user = data as User

// ✅ Validate at boundaries
const user = userSchema.parse(data)
```

### Async Error Handling

**Rule:** All promises must be awaited or explicitly handled. Unhandled promise rejections crash processes.

```typescript
// ❌ Fire-and-forget swallows errors
async function notify(user: User) {
  sendEmail(user.email)
}

// ✅ Explicit fire-and-forget with logging
async function notify(user: User) {
  sendEmail(user.email).catch(err => logger.error('email failed', { err }))
}
```

**Rule:** Never return unions of error types. Use exceptions or Result types.

```typescript
// ❌ Caller must check every return
function divide(a: number, b: number): number | 'DIVIDE_BY_ZERO'

// ✅ Throw for exceptional cases
function divide(a: number, b: number) {
  if (b === 0) throw new Error('DIVIDE_BY_ZERO')
  return a / b
}
```

### Dependency Discipline

**Rule:** Before adding a dependency, check if native functionality exists.

```typescript
// ❌ New dependency for trivial operation
import { isNil } from 'lodash'
if (isNil(value)) { ... }

// ✅ Native is sufficient
if (value == null) { ... }
```

**Check:** Does this package solve a problem we actually have, or a problem we imagine having?

### Testing Policy

We prioritize architectural correctness and database constraints over unit test coverage.

**When tests ARE required:**
- Complex state machines
- Multi-step financial calculations
- Integration points with external systems

**When tests are NOT required:**
- Code following the Recipe pattern
- Validation delegated to schemas or DB constraints
- CRUD operations

Reviewers: Do not flag missing test coverage unless a standards section explicitly requires tests.
</section>

<section name="frontend">
## Frontend

Standards specific to frontend code (anything in `apps/` folder).

### Timezone Authority

**Rule:** Frontend owns timezone handling. Backend receives ISO strings.

```typescript
// ✅ Frontend sends timezone-aware boundaries
POST /api/transactions {
  startDate: '2024-01-01T05:00:00Z',
  endDate: '2024-01-02T04:59:59Z'
}

// ❌ Backend calculates day boundaries
const startOfDay = new Date().setHours(0, 0, 0, 0)
```

### Storage-UI Separation

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

### Data Minimalism

**Rule:** Return primitive fields only. UI composes derived values.

```typescript
// ❌ Computed in API
return { fullName: `${user.firstName} ${user.lastName}` }

// ✅ Primitives only
return { firstName: user.firstName, lastName: user.lastName }
```

### Money Display

**Rule:** Always display money values as strings. Never use `Number` for financial amounts.

```typescript
// ❌ Number loses precision
const display = `$${amount.toFixed(2)}`

// ✅ String preserves precision
const display = `$${formatMoney(amount)}`
```

### Input Validation

**Rule:** Frontend does light validation (constraints). Backend does full validation (error generation).

```typescript
// ✅ Frontend: Light validation via input constraints
<input
  type="number"
  maxLength={10}
  pattern="[0-9]*"
  min={0}
  max={100}
/>

// ✅ Frontend: Prevent obviously wrong input
<Input
  type="number"
  onChange={(e) => {
    // Block non-numeric input at keystroke level
    if (!/^\d*\.?\d*$/.test(e.target.value)) return
    setValue(e.target.value)
  }}
/>

// ✅ Backend: Full validation with business rules
const userSchema = z.object({
  age: z.number().min(0).max(120, 'Age must be realistic'),
  email: z.string().email('Invalid email format'),
  username: z.string()
    .min(3, 'Username must be at least 3 characters')
    .max(20, 'Username cannot exceed 20 characters')
    .regex(/^[a-zA-Z0-9_]+$/, 'Username can only contain letters, numbers, and underscores')
})
```

**Rule:** Frontend shows backend error messages. Don't duplicate validation logic.

```typescript
// ❌ Frontend duplicates backend validation
const validateForm = (data: UserInput) => {
  if (data.username.length < 3) return 'Username too short'  // ❌ Duplicates backend
  if (data.age < 0) return 'Age cannot be negative'           // ❌ Duplicates backend
  return null
}

// ✅ Frontend shows backend errors
const onSubmit = async (data: UserInput) => {
  try {
    await api.createUser(data)
  } catch (err) {
    if (err instanceof TRPCError) {
      setError(err.message)  // ✅ Display backend's error message
    }
  }
}
```

**Rationale:** Frontend constraints improve UX (immediate feedback). Backend validation is the source of truth for error messages. Duplicating validation logic causes drift and maintenance burden.

### Input Validation

**Rule:** Frontend does light validation (constraints). Backend does full validation (error messages).

```typescript
// ✅ Frontend: Input constraints (prevent invalid input)
<Input
  type="number"
  maxLength={10}           // Prevent typing more than 10 chars
  onKeyDown={numbersOnly}   // Block non-numeric keys
/>

// ✅ Frontend: Trust backend for actual errors
const { mutate, error } = trpc.user.update.useMutation()
// error.message comes from backend validation

// ❌ Frontend: Duplicating backend validation logic
const schema = z.object({
  name: z.string().min(1, 'Name is required'),  // ❌ Backend already validates this
})
```

**Rationale:** Frontend constraints improve UX (immediate feedback, prevent invalid input). Backend validation is authoritative and generates user-facing errors. Duplicating validation logic causes drift when rules change.

### No Defensive Bloat

**Rule:** Don't re-validate data passed between components. Validate at the edge, trust downstream.

```typescript
// ❌ Re-validating props in every component
function UserCard({ user }: { user: User }) {
  if (!user || !user.id) return null  // ❌ Parent already validated
  // ...
}

// ❌ Defensive parsing in render
function UserList({ users }: { users: User[] }) {
  const validUsers = users.filter(u => u.id && u.name)  // ❌ Trust the source
  // ...
}

// ✅ Validate once at the edge (API response), trust everywhere else
function UserCard({ user }: { user: User }) {
  // user is guaranteed valid by the API layer
  return <div>{user.name}</div>
}
```

### Discriminated Unions for State

**Rule:** Use discriminated unions for component state. Never use multiple booleans.

```typescript
// ❌ Multiple booleans can represent impossible states
type State = {
  isLoading: boolean
  isError: boolean
  isSuccess: boolean
}
// Impossible: isLoading: true && isError: true

// ✅ Discriminated union - states are mutually exclusive
type State =
  | { status: 'loading' }
  | { status: 'error'; error: Error }
  | { status: 'success'; data: User }

// TypeScript narrows correctly
function render(state: State) {
  switch (state.status) {
    case 'loading': return <Spinner />
    case 'error': return <Error message={state.error.message} />
    case 'success': return <UserCard user={state.data} />
  }
}
```

**Rationale:** Booleans allow impossible states. Discriminated unions make invalid states unrepresentable and enable exhaustive type narrowing.
</section>

<section name="backend">
## Backend

Standards specific to backend code (anything in `packages/` folder).

### Financial Integrity

**Policy: Zero-Tolerance. Violation = Automatic REJECT.**

#### BigInt-Only Math

**Rule:** All financial calculations use `BigInt`. No exceptions.

```typescript
// ❌ Precision loss
const total = parseFloat(a) + parseFloat(b)

// ✅ Exact arithmetic
const total = BigInt(a) + BigInt(b)
```

#### String Transport

**Rule:** Money values are strings at every API boundary.

```typescript
// ❌ Number in transport
interface PaymentResponse { amount: number }

// ✅ String transport
interface PaymentResponse { amount: string }
```

**Exception:** Number conversion is allowed only at the final call to a 3rd-party SDK that requires it.

#### No Logic Wrappers

**Rule:** Use native operators directly. Do not abstract `BigInt` comparison.

```typescript
// ❌ Unnecessary wrapper
if (compareNumericStrings(a, b) > 0) { ... }

// ✅ Native is clearer
if (BigInt(a) > BigInt(b)) { ... }
```

### No Interior Guard Spam

**Rule:** If the database enforces `NOT NULL`, do not write `value ?? fallback` in application code.

```typescript
// ❌ DB has NOT NULL, but code guards anyway
const name = user.name ?? 'Unknown'

// ✅ Trust the constraint
const name = user.name
```

**Exception:** Only guard when the source is genuinely unreliable (external APIs, user input before validation).

### Time Handling

**Rule:** Backend must not interpret timezones. Store and retrieve ISO strings only.

```typescript
// ❌ Backend calculates day boundaries
const startOfDay = new Date().setHours(0, 0, 0, 0)

// ✅ Frontend sends timezone-aware boundaries
// Backend just stores/retrieves
```

**Rule:** Backend must not import `luxon` or `date-fns`. Use native `Date` and `Intl`.

**Rationale:** Timezone logic belongs in the presentation layer. Backend stores and retrieves.

### Updated At Handling

**Rule:** Database manages `updatedAt`. Do not send in mutation payloads.

```typescript
// ❌ Manual update
await db.update(users).set({ ...input, updatedAt: new Date() })

// ✅ Let DB handle it
await db.update(users).set(input) // DB trigger updates updatedAt
```

### API Contracts

#### Status Over Boolean

**Rule:** HTTP status and response presence indicate success. Remove `success: true`.

```typescript
// ❌ Redundant
return { success: true, data: user }

// ✅ Implicit success
return user
```

**Rule:** tRPC procedures return data directly. Success is implicit—errors throw.

```typescript
// ❌ Wrapping in success object
export const updateUser = protectedProcedure
  .input(updateSchema)
  .mutation(async ({ input }) => {
    const user = await db.users.update(input)
    return { success: true, user }  // ❌ Redundant
  })

// ✅ Return data directly
export const updateUser = protectedProcedure
  .input(updateSchema)
  .mutation(async ({ input }) => {
    return db.users.update(input)  // ✅ tRPC handles success/error
  })
```

**Rationale:** tRPC clients receive data on success, catch errors on failure. Wrapping in `{ success: true }` adds nothing and forces clients to unwrap.

**tRPC Note:** tRPC procedures already indicate success/failure through response presence. Adding `success: true` is redundant noise.

```typescript
// ❌ Redundant wrapper in tRPC
.updateMutation: protectedProcedure
  .input(updateSchema)
  .mutation(async ({ input }) => {
    await updateUser(input)
    return { success: true }  // ❌ tRPC already signals success
  })

// ✅ Return data or nothing
.updateMutation: protectedProcedure
  .input(updateSchema)
  .mutation(async ({ input }) => {
    await updateUser(input)
    return { id: input.id }  // Return what's useful, or omit return
  })
```

#### Return Primitives

**Rule:** Return primitive fields. Let callers compose derived values.

```typescript
// ❌ Computed in API
return { fullName: `${user.firstName} ${user.lastName}` }

// ✅ Primitives only
return { firstName: user.firstName, lastName: user.lastName }
```

### Endpoint Naming

**Rule:** Endpoint names use a single action word that precisely describes the operation. Format: `resource.subresource.action`.

```typescript
// ✅ Clear, action-oriented endpoints
user.profile.update      // Update user profile
user.profile.get         // Get user profile
user.transaction.list    // List user transactions
user.transaction.create  // Create user transaction
order.cancel             // Cancel an order
payment.refund           // Refund a payment

// ❌ Vague or missing action
user.profile             // What operation? Get? Update?
user.transaction         // Ambiguous
processOrder             // Missing resource context
```

**Rationale:** Action words make the operation explicit at a glance. Resources (user, transaction) provide context; actions (update, list, create) specify intent.

### Database Query Patterns

#### No N+1 Queries

**Rule:** When fetching related data, batch the query.

```typescript
// ❌ N+1 queries
const users = await db.select().from(users)
for (const user of users) {
  user.orders = await db.select().from(orders).where(eq(orders.userId, user.id))
}

// ✅ Single query with join
const users = await db.select()
  .from(users)
  .leftJoin(orders, eq(users.id, orders.userId))
```

**Rationale:** Each database round-trip adds latency. One query with joins is faster than N+1 queries. However, we must always prioritize readability over raw performance.
</section>