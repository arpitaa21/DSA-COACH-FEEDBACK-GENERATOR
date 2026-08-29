# Binary Search

## When to use it
Any time you can turn the problem into "find the boundary in a monotonic
(sorted, or sorted-like) search space." That includes searching a sorted
array, but also "search on the answer" problems - e.g. minimizing the maximum
load, or finding the smallest value for which a condition first becomes true.

## Core idea
Maintain `lo` and `hi` bounds. At each step, check the midpoint and use the
result to eliminate half the remaining search space. The key invariant to get
right: does the loop use `lo < hi` or `lo <= hi`, and does `mid` get included
or excluded on each branch? Mixing these up is the single most common bug.

## Two common templates
- **Exact match search**: `lo <= hi`, return the index directly when
  `arr[mid] == target`, otherwise move `lo = mid + 1` or `hi = mid - 1`.
- **Boundary search** (first/last True in a monotonic boolean space):
  `lo < hi`, narrow toward the boundary, and check the final `lo` after the
  loop rather than returning from inside it.

## Complexity
O(log n) time, O(1) space (iterative) or O(log n) space (recursive, due to
the call stack).

## Common mistakes
- Using `lo < hi` but never actually reaching the last element because the
  loop exits one step early - this shows up as "off by one," specifically
  missing the boundary when the target is the very last valid element.
- Integer overflow computing `mid` in languages with fixed-width integers -
  use `lo + (hi - lo) // 2` instead of `(lo + hi) // 2`.
- Applying it to data that isn't actually sorted/monotonic along the axis
  you're searching.
