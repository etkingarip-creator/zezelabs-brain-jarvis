# Runtime Optimization Plan

## Top 10 Optimizations
1. **Lazy Loading of Models**: `faster_whisper` and `google.generativeai` in `jarvis.py` should be lazy-loaded only when `voice` or `vision` is actively requested.
2. **Remove Polling**: Use WebSockets instead of `httpx` polling loops where possible.
3. **Centralized Registries**: Move all queue definitions and tool manifests to a centralized `core/registry/` structure.
4. **Purge Backups**: Delete or ignore `OLD_GIT_BACKUP_DO_NOT_PUSH` to reduce file indexer lag.
5. **Consolidate ENV Access**: Use `pydantic-settings` to manage ENV variables rather than scattered `os.getenv()`.
6. **Thread Pools**: Replace bare `threading.Thread` with `ThreadPoolExecutor` for bounded concurrency.
7. **Database Connection Pooling**: Ensure `redis.Redis()` uses a connection pool.
8. **RabbitMQ Heartbeats**: Ensure `pika` blocking connections have heartbeats enabled to avoid dropped connections.
9. **Avoid `subprocess.Popen`**: Standardize on `subprocess.run` wrapped via ClawdeProcessAdapter.
10. **Dataset Pruning**: Compress JSONL exports in `Zeze-Academy` to avoid memory bloat during dataset generation.

## Proposed New Structure
```
core/registry/
  - departments.py
  - queues.py
  - features.py
  - env.py
```
