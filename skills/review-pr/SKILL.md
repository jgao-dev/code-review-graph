---
name: review-pr
description: Review a PR or branch diff using the knowledge graph for full structural context. Outputs a structured review with blast-radius analysis.
argument-hint: "[PR number or branch name]"
---

# Review PR

Perform a comprehensive code review of a pull request or branch diff using the knowledge graph.

**Token optimization:** Before starting, call `get_docs_section_tool(section_name="review-pr")` for the optimized workflow. Never include full files unless explicitly asked.

## Steps

1. **Identify the changes** for the PR:
   - If a PR number or branch is provided, use `git diff main...<branch>` to get changed files
   - Otherwise auto-detect from the current branch vs main/master

2. **Update the graph** by calling `build_or_update_graph_tool(base="main")` to ensure the graph reflects the current state.

3. **Get the full review context** by calling `get_review_context_tool(base="main", include_standards=True)`:
   - This uses `main` (or the specified base branch) as the diff base
   - Returns all changed files across all commits in the PR
   - **Auto-loads relevant standards** based on file patterns (see below)

4. **Load additional standards** if needed. Standards are auto-selected based on file patterns:
   | File Pattern | Sections Loaded |
   |--------------|-----------------|
   | `*financial*`, `*money*`, `*payment*`, `*billing*` | phase-1 (Financial Integrity) |
   | `*time*`, `*date*`, `*schedule*` | phase-2 (Time & Frontend Authority) |
   | `*api*`, `*route*`, `*handler*` | phase-3 (API Contracts) |
   | `*util*`, `*helper*`, `*lib*` | phase-0, phase-4 (Structure + Utility Purge) |
   | All files | summary (Pre-Submit Checklist) |

   Override with: `get_review_standards_tool(section_name="phase-X")`

5. **Analyze impact** by calling `get_impact_radius_tool(base="main")`:
   - Review the blast radius across the entire PR
   - Identify high-risk areas (widely depended-upon code)

6. **Deep-dive each changed file**:
   - Read the full source of files with significant changes
   - Check against loaded standards sections for violations
   - Use `query_graph_tool(pattern="callers_of", target=<func>)` for high-risk functions
   - Check for breaking changes in public APIs

7. **Generate structured review output**:

   ```
   ## PR Review: <title>

   ### Summary
   <1-3 sentence overview>

   ### Risk Assessment
   - **Overall risk**: Low / Medium / High
   - **Blast radius**: X files, Y functions impacted

   ### Standards Compliance
   - Phase 0 (Structure): ✅ Pass / ⚠️ Issues found
   - Phase 1 (Financial): ✅ Pass / ⚠️ Issues found
   - Phase 2-4: (if applicable)

   ### File-by-File Review
   #### <file_path>
   - Changes: <description>
   - Impact: <who depends on this>
   - Issues: <bugs, style, concerns>
   - Standards violations: <specific phase violations>

   ### Recommendations
   1. <actionable suggestion>
   2. <actionable suggestion>
   ```

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

## Testing Policy

**Do not suggest adding tests.** Focus on standards compliance and logic correctness. Only mention testing if explicitly required by a standards section. Do not flag missing test coverage as an issue.

## Tips

- For large PRs, focus on the highest-impact files first (most dependents)
- Use `semantic_search_nodes_tool` to find related code the PR might have missed
- Check if renamed/moved functions have updated all callers
- Apply standards systematically: start with Phase 0 (structure), then Phase 1 (financial), etc.
- Standards are auto-loaded based on file names - financial files get phase-1 automatically