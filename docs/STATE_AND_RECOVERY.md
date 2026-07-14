# State and recovery

Product state uses SQLite with foreign keys, WAL mode, a busy timeout, transactional stage completion, schema migrations, event hash chains, checkpoints, and expiring worker leases. Recovery resumes from the last committed stage. Tampered event or proof chains fail closed. Repeated stage commands are idempotent.
