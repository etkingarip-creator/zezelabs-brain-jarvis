# Architecture Conflict Matrix

1. **Router vs Department Queues**: No conflicts. Keywords are specifically mapped.
2. **PolicyEngine vs Adapter**: Both deny `live_trade` and `withdrawal`. No mismatch found.
3. **Workspace Limits**: Generated files stay inside `dogfood_reports` or `paper_state`, respecting `workspace_root`.
4. **App Factory vs Clawde Adapter**: App Factory generates files safely without triggering raw shell execution.
