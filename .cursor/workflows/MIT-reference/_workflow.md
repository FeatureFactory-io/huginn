# Manage Iteration (MIT)

**Playbook**: FeatureFactory v13.0 (Released)
**Workflow ID**: 17
**Local prefix**: `MIT-reference`
**Description**: Jedao-driven autonomous execution workflow. Activates from the PIT-produced execution manifest, executes scenarios sequentially within conflict-safe parallel groups, detects and classifies drift events, surfaces escalations to the human, course-corrects the manifest when needed, and closes the iteration with a GitHub Release, Lessons Learned document, and EST-08 sprint rebaseline.
**Phase Organization**: Uses phases
**Total Activities**: 4
**Export Date**: 2026-05-05 17:06 UTC

## Activities

See individual activity files in this directory.

## Editing Instructions

- **Add activity**: Create new file with pattern `MIT-reference-XX-Name.md`
- **Remove activity**: Delete the .md file
- **Reorder**: Rename files to change order numbers
- **Edit content**: Modify description, guidance, dependencies
- **Change phase**: Update the Phase field

After editing, use Mimir **`import_workflow_from_local`** (`workflow_id` **17**, `source_directory` = this directory, e.g. `.cursor/workflows/MIT-reference`).
