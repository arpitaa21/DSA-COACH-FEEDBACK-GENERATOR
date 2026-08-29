# Two Pointers

## When to use it
Reach for two pointers whenever the input is a sorted array, a linked list, or
you're comparing elements from opposite ends of a sequence. Classic signal: the
problem asks for a pair, triplet, or subarray that satisfies a sum or ordering
condition, and a brute-force solution would be O(n^2).

## Core idea
Keep two indices - often one at each end (`left`, `right`) or one trailing
another (`slow`, `fast`) - and move them based on a comparison, instead of
checking every pair explicitly.

## Common variants
- **Opposite ends, sorted array**: move `left` up or `right` down depending on
  whether the current sum is too small or too large (e.g. Two Sum II, container
  with most water).
- **Fast/slow pointers**: cycle detection in a linked list, finding the middle
  node in one pass.
- **Same-direction (sliding) two pointers**: used for removing duplicates in
  place, or partitioning an array around a pivot.

## Complexity
Typically O(n) time, O(1) extra space - that's the whole appeal over a nested
loop. Watch out: if the array isn't sorted and the problem needs sortedness,
you pay O(n log n) up front for the sort.

## Common mistakes
- Forgetting to skip duplicate values when the problem asks for unique results.
- Off-by-one errors in the loop condition (`left < right` vs `left <= right`).
- Applying it to a problem that actually needs a hash map instead (e.g. Two Sum
  on an *unsorted* array with index requirements - sorting would lose the
  original indices).
