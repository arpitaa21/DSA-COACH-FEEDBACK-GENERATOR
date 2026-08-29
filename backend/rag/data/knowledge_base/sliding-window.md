# Sliding Window

## When to use it
Use a sliding window whenever the problem talks about a *contiguous* subarray
or substring and asks for something optimal - longest, shortest, or a count -
under some constraint (sum, distinct characters, at most K of something).

## Core idea
Maintain a window defined by `left` and `right` indices. Expand `right` to
grow the window, and shrink from `left` when the window violates the
constraint. Each element enters and leaves the window at most once, which is
what gives the O(n) bound instead of the O(n^2) you'd get by checking every
subarray.

## Fixed vs variable window
- **Fixed size window** (e.g. "max sum of any subarray of size k"): slide by
  one each step, add the new element, remove the one that fell out.
- **Variable size window** (e.g. "smallest subarray with sum >= target",
  "longest substring with at most K distinct characters"): grow `right` until
  the constraint breaks, then shrink `left` until it's valid again.

## Complexity
O(n) time, O(1) to O(k) space depending on what you're tracking in the window
(a running sum vs. a frequency map of characters).

## Common mistakes
- Shrinking the window with an `if` instead of a `while`, which only removes
  one element when the window might be invalid by more than one.
- Forgetting to update the "best answer" *inside* the loop instead of only
  once at the end.
- Using a window when the subarray doesn't need to be contiguous - that's a
  different pattern (subsequence, not substring).
