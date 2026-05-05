# Plan Iteration (PIT)

**Playbook**: FeatureFactory v13.0 (Released)
**Workflow ID**: 16
**Local prefix**: `PIT-reference`
**Description**: Human-AI composite planning session that transforms backlog scenarios into a fully-planned, skeleton-first execution manifest. Reads lessons learned from prior iterations, selects the iteration goal, sequences scenarios on a conflict-aware critical path, runs BPE-01 + creates code skeletons per scenario, builds a machine-readable YAML manifest, publishes Milestone + Issues to GitHub, and obtains human acceptance before handing off to Jedao for MIT execution.
**Phase Organization**: Uses phases
**Total Activities**: 4
**Export Date**: 2026-05-05 17:06 UTC

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern `PIT-reference-XX-Name.md`
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use Mimir **`import_workflow_from_local`** (`workflow_id` **16**, `source_directory` = this directory, e.g. `.cursor/workflows/PIT-reference`).
