
## 2024-05-18 - Heavy List Component Re-renders
**Learning:** Large data tables (FlipTable, LongTermFlipTable) that render hundreds of nested elements per row are huge bottlenecks if not memoized, as parent components (like Views) frequently re-render on polling intervals or minor state updates.
**Action:** Always wrap heavy list/table components and their individual row/cell sub-components with `React.memo` when they receive large arrays of data that don't change on every parent re-render.

## 2026-05-19 - React.memo Invalidated by Inline Functions
**Learning:** Even if heavy list components (like FlipTable) are wrapped in `React.memo`, passing inline functions (e.g., `onShowPriceHistory={(item) => ...}`) from parent components completely invalidates the memoization. This is because a new function reference is created on every parent render, forcing the heavy child component to re-render.
**Action:** When passing callbacks to memoized heavy components, ALWAYS wrap them in `useCallback` to preserve function references and maintain the `React.memo` optimization.
