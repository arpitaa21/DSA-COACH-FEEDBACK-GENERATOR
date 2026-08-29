# Dynamic Programming

## When to use it
Look for overlapping subproblems and optimal substructure: the problem asks
for a count, a minimum/maximum, or a yes/no reachability, and a brute-force
recursive solution would recompute the same subproblem many times.

## Core idea
Define a state (what does `dp[i]`, or `dp[i][j]`, actually represent?), a
recurrence relating that state to smaller states, and a base case. Then either
memoize the recursive solution (top-down) or build a table iteratively
(bottom-up).

## How to approach a new DP problem
1. Write the brute-force recursive solution first, in plain language: "what
   choice am I making at each step, and what smaller version of the problem
   does each choice leave me with?"
2. Identify what varies between recursive calls - that's your state.
3. Check whether the same state gets recomputed - if yes, DP helps.
4. Decide top-down (easier to derive, some recursion overhead) vs bottom-up
   (usually faster, needs the iteration order figured out).

## Complexity
Typically O(states x transitions). A 1D DP over n elements with O(1)
transition is O(n); a 2D DP (e.g. two strings of length m and n) is often
O(m*n).

## Common mistakes
- Defining the state ambiguously (e.g. "dp[i] = best answer" without saying
  best answer *ending where* / *using what*).
- Forgetting a base case, causing index errors or wrong answers for small
  inputs.
- Using O(n^2) space when a rolling array (only keeping the last 1-2 rows)
  would bring it down to O(n).
