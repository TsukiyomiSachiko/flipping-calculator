
## 2024-05-18 - Heavy List Component Re-renders
**Learning:** Large data tables (FlipTable, LongTermFlipTable) that render hundreds of nested elements per row are huge bottlenecks if not memoized, as parent components (like Views) frequently re-render on polling intervals or minor state updates.
**Action:** Always wrap heavy list/table components and their individual row/cell sub-components with `React.memo` when they receive large arrays of data that don't change on every parent re-render.
