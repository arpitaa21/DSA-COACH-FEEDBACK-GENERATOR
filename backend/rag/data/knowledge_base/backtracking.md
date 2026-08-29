# Backtracking

## When to use it
Problems that ask for *all* valid combinations, permutations, subsets, or
placements satisfying some constraint (N-Queens, Sudoku, generating
parentheses, subsets/permutations of a set).

## Core idea
Build a solution incrementally, one choice at a time. After each choice,
recurse into the next decision. If a partial solution can no longer lead to a
valid full solution (a constraint is violated), stop exploring that branch
immediately ("prune") and undo the last choice before trying the next option.

## The three-part shape
1. **Choose** - pick one option at the current decision point.
2. **Explore** - recurse into the next decision with that choice applied.
3. **Un-choose** - revert the choice before trying the next option, so
   sibling branches don't see stale state.

## Complexity
Often exponential in the worst case (that's inherent to enumerating all valid
configurations), but good pruning can cut the practical runtime drastically.
The theoretical bound is usually stated as O(branching_factor^depth).

## Common mistakes
- Forgetting the "un-choose" step, so state leaks between branches (a classic
  bug: mutating a shared list without popping/removing after the recursive
  call returns).
- Not pruning early enough - checking the constraint only once the full
  candidate is built instead of as soon as it's violated.
- Copying the current partial solution incorrectly (shallow copy of a list
  containing mutable objects) when adding it to the results.
