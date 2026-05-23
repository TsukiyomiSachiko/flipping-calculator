
## 2024-05-18 - Heavy List Component Re-renders
**Learning:** Large data tables (FlipTable, LongTermFlipTable) that render hundreds of nested elements per row are huge bottlenecks if not memoized, as parent components (like Views) frequently re-render on polling intervals or minor state updates.
**Action:** Always wrap heavy list/table components and their individual row/cell sub-components with `React.memo` when they receive large arrays of data that don't change on every parent re-render.

## 2026-05-19 - React.memo Invalidated by Inline Functions
**Learning:** Even if heavy list components (like FlipTable) are wrapped in `React.memo`, passing inline functions (e.g., `onShowPriceHistory={(item) => ...}`) from parent components completely invalidates the memoization. This is because a new function reference is created on every parent render, forcing the heavy child component to re-render.
**Action:** When passing callbacks to memoized heavy components, ALWAYS wrap them in `useCallback` to preserve function references and maintain the `React.memo` optimization.

## 2026-05-20 - In-Memory Caching for File-Based API Reponses
**Learning:** The application's `CacheManager` was reading JSON responses from disk for every backend API request when serving cached data. This led to thousands of repetitive disk reads (JSON parsing and I/O) on hot paths like `FlipService.get_profitable_flips`, becoming a major bottleneck specific to this architecture.
**Action:** Always complement file-based caches with an in-memory dictionary layer that checks `os.path.getmtime` to determine if a fresh disk read is truly necessary, vastly accelerating high-frequency API endpoints without sacrificing data freshness.

## 2024-05-23 - `copy.deepcopy()` is Too Slow for Large JSON API Caches
**Learning:** Returning cached API responses (like OSRS Wiki prices dict) by using `copy.deepcopy()` on a dict in memory takes over ~0.25s per request. This creates a severe backend performance bottleneck when many routes need fresh data simultaneously.
**Action:** Always prefer caching the raw serialized JSON string and calling `json.loads(string)` upon retrieval. It is written in C and is >10x faster than navigating a large nested python dict with `copy.deepcopy()`.
