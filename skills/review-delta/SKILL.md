---
name: review-delta
description: Review only changes since last commit using impact analysis. Token-efficient delta review with automatic blast-radius detection.
argument-hint: "[file or function name]"
---

# Review Delta

Perform a focused, token-efficient code review of only the changed code and its blast radius.

**Token optimization:** Before starting, call `get_docs_section_tool(section_name="review-delta")` for the optimized workflow. Use ONLY changed nodes + 2-hop neighbors in context.

## Steps

1. **Ensure the graph is current** by calling `build_or_update_graph_tool()` (incremental update).

2. **Get review context** by calling `get_review_context_tool(include_standards=True)`. This returns:
   - Changed files (auto-detected from git diff)
   - Impacted nodes and files (blast radius)
   - Source code snippets for changed areas
   - Review guidance (wide impact warnings, inheritance concerns)
   - **Auto-selected standards** based on file patterns (see below)

3. **Load additional standards** if needed. Standards are auto-selected based on file patterns:
   | File Pattern | Sections Loaded |
   |--------------|-----------------|
   | `*financial*`, `*money*`, `*payment*`, `*billing*` | phase-1 (Financial Integrity) |
   | `*time*`, `*date*`, `*schedule*` | phase-2 (Time & Frontend Authority) |
   | `*api*`, `*route*`, `*handler*` | phase-3 (API Contracts) |
   | `*util*`, `*helper*`, `*lib*` | phase-0, phase-4 (Structure + Utility Purge) |
   | `*constant*`, `*config*` | phase-0 (Structural Integrity) |
   | All files | summary (Pre-Submit Checklist) |

   Override with: `get_review_standards_tool(section_name="phase-X")`

4. **Analyze the blast radius** by reviewing the `impacted_nodes` and `impacted_files` in the context. Focus on:
   - Functions whose callers changed (may need signature/behavior verification)
   - Classes with inheritance changes (Liskov substitution concerns)
   - Files with many dependents (high-risk changes)

5. **Get LSP diagnostics** by calling `mcp__ide__getDiagnostics()` (no arguments for all files, or pass a file URI for specific files). This returns:
   - Syntax errors
   - Type errors
   - Linting warnings
   - Unused variables/imports
   - Other language-specific issues

6. **Perform the review** using the context, standards, and diagnostics. For each changed file:
   - Review the source snippet for correctness, style, and potential bugs
   - Check against loaded standards sections for violations
   - Check if impacted callers/dependents need updates
   - Verify no unresolved diagnostics remain in changed files

7. **Report findings** in a structured format:
   - **Summary**: One-line overview of the changes
   - **Risk level**: Low / Medium / High (based on blast radius)
   - **Standards violations**: Organized by phase (if any)
   - **LSP diagnostics**: Unresolved errors/warnings in changed files
   - **Issues found**: Bugs, style issues, standards violations
   - **Blast radius**: List of impacted files/functions
   - **Recommendations**: Actionable suggestions

## Standards Reference

Common sections available:
- `phase-0`: Structural Integrity & Anti-Bloat
- `phase-0.5`: Anti-Defensive Bloat Rule
- `phase-0.6`: Recipe Readability Rule
- `phase-1`: Financial Integrity (BigInt only, no parseFloat)
- `phase-2`: Time & Frontend Authority
- `phase-3`: API Contracts & Transport
- `phase-4`: Utility Purge
- `summary`: Pre-Submit Checklist (includes Testing Policy)

### Testing Policy Note
If the codebase lacks tests, do not suggest adding them. Focus on standards compliance and logic correctness. Only mention testing if explicitly required by the loaded standards sections.

## Advantages Over Full-Repo Review

- Only sends changed + impacted code to the model (5-10x fewer tokens)
- Automatically identifies blast radius without manual file searching
- Provides structural context (who calls what, inheritance chains)
- Auto-loads relevant coding standards based on file patterns
