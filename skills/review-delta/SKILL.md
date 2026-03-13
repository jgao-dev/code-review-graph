---
name: review-delta
description: Review only changes since last commit using impact analysis. Token-efficient delta review with automatic blast-radius detection.
argument-hint: "[file or function name]"
---

# Review Delta

Expert code review for uncommitted changes. Reviews changes since last commit with blast-radius analysis and standards enforcement.

## Step 1: Get Base

Use `HEAD` as the base for delta review:
- Auto-detect changed files from `git diff HEAD`
- For staged changes: `git diff --cached`
- For all uncommitted changes: `git diff HEAD`

## Step 2-3: Build Context

```
build_or_update_graph_tool(base="HEAD")
get_review_context_tool(base="HEAD")
get_docs_section_tool(section_name="principles")
get_docs_section_tool(section_name="frontend")  # if apps/** changed
get_docs_section_tool(section_name="backend")   # if packages/** changed
```

## Step 4: Check LSP Diagnostics

```
mcp__ide__getDiagnostics()
```

Returns: syntax errors, type errors, linting warnings, unused variables/imports, other language-specific issues.

## Step 5: Apply Standards

Standards are loaded in Step 2-3. For each changed file:

1. Apply **principles** section to all files
2. Apply **frontend** section to `apps/**` files
3. Apply **backend** section to `packages/**` files

**Be exhaustive.** Find every violation. No issue is too small. A single-letter typo, a missed optimization, a minor inconsistency—all must be flagged.

## Step 6: Generate Report

```
## Delta Review: <changed files>

### Context
- Base: HEAD (changes since last commit)

### Standards Violations
- file.ts:45: `any` type - use unknown
- api.ts:120: type assertion - validate instead
(If none: ✓ All standards verified)

### Other Issues
<logic bugs, security, performance>

### Blast Radius
<X files, Y functions impacted>
```

**Skip positives. Focus on finding every violation.**

## Guidelines

1. **Base is HEAD** - Review changes since last commit.
2. **All violations block commit** - No severity classification.
3. **Flag with file:line** - Always include location and pattern.
4. **Check LSP diagnostics** - Include unresolved errors/warnings.
5. **Be nitpicky** - Find every violation, no matter how small. Skip positives.
6. **No test suggestions** - Unless required by standards.
7. **Token efficiency** - Use graph tools for impacted code only.

## Graph Tools

```
query_graph_tool(pattern="callers_of", target="fn_name")
query_graph_tool(pattern="importers_of", target="file_path")
semantic_search_nodes_tool(query="auth", kind="Function")
```