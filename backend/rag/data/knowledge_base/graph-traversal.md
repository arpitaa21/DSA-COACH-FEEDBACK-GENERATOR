# Graph Traversal (BFS / DFS)

## When to use it
Any problem phrased in terms of connections, reachability, shortest number of
steps, or "explore all X" over a graph, grid, or implicit graph (e.g. word
transformations, state spaces).

## BFS vs DFS
- **BFS** explores level by level using a queue - use it when you need the
  *shortest path* in an unweighted graph, or the minimum number of steps.
- **DFS** explores as deep as possible before backtracking, using a stack
  (explicit or via recursion) - use it for connectivity, cycle detection,
  topological sort, or when you need to explore *all* paths rather than the
  shortest one.

## Core idea
Track visited nodes to avoid infinite loops on cyclic graphs. For BFS, mark a
node visited the moment it's enqueued, not when it's dequeued, or you can
enqueue the same node multiple times.

## Complexity
O(V + E) for both, where V is vertices and E is edges - each node and edge is
visited a constant number of times.

## Common mistakes
- Marking nodes visited on dequeue instead of enqueue in BFS, which can blow
  up the queue size and, in the worst case, correctness on graphs with many
  cross-edges into the same node.
- Forgetting a visited set entirely on a cyclic graph, causing infinite
  recursion/looping.
- Using DFS when the problem actually needs shortest path (BFS) - depth-first
  order doesn't guarantee the first path found is the shortest one.
