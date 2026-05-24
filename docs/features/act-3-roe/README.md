# Act 3 — Rules of Engagement (Gherkin)

Feature files in this folder specify **ROE-\*** screens (LIST+FIND, CREATE, VIEW, EDIT, DELETE).

**Product narrative and cross-act context** live in [`docs/features/user_journey.md`](../user_journey.md) (Act 3 section).

**UX alignment**

- **LIST+FIND** (`roe-list-find.feature`): table columns **Name | Author | Latest version | Used by | Updated**; **Name** opens VIEW; **Edit / Clone / Delete** live in the row **overflow menu** (no Actions column). **Header toolbar:** disabled **Get RoE from Mimir** (Mimir icon, coming soon) beside primary **+ New Rules of Engagement**. Matches IA §5.2 — LIST+FIND Table in [`docs/ux/IA_guidelines.md`](../../ux/IA_guidelines.md).
- **VIEW** (`roe-view.feature`): **Rules of Engagement** and **Versions** tabs (same card-tab pattern as Project detail — IA §5.2 Detail VIEW tabs); **`[Validate RoE]`** in the **page header toolbar** (IA §3.4) with results collapsed above the tab card; diagnostic catalog drift only (not AI).
- **CREATE / EDIT**: Workflow is **markdown** with a preview that renders headings (not raw `##`).
