# AetherEdge Database — Schema & Design

## Overview

This document describes the SQLite database schema for the AetherEdge server, including tables, relationships, and design rationale.

---

## 🗄️ Database Choice

### SQLite (Part I)

**Why SQLite for Part I?**
1. **Zero configuration**: No separate server process
2. **File-based**: Single database file, easy to backup
3. **Sufficient scale**: Prototype scale handles SQLite easily
4. **Migration path**: Can upgrade to PostgreSQL for Part II
5. **Development speed**: No infrastructure setup required

### PostgreSQL (Part II)

**Why PostgreSQL for Part II?**
1. **Concurrency**: Better for many concurrent edge nodes
2. **Scalability**: Horizontal sharding and replication
3. **Advanced types**: JSONB, arrays, custom types
4. **Performance**: Indexes, query optimization
5. **Reliability**: ACID transactions, replication

---

## 📊 Schema

### Tables

```
nodes
├── id (PK, auto-increment)
├── node_id (UNIQUE)           # Edge node identifier
├── hostname                   # Human-readable hostname
├── os                         # Operating system name
├── os_version, kernel_version
├── cpu_brand, cpu_cores
├── total_memory               # In bytes
├── version                    # Software version
├── arch                       # CPU architecture
├── status                     # ONLINE, OFFLINE, DEGRADED
├── last_seen                  # Timestamp of last heartbeat
├── created_at, updated_at
└── (Relationship) → telemetry

telemetry
├── id (PK, auto-increment)
├── node_id (FK → nodes.id)
├── timestamp                  # When data was collected
├── cpu_usage, cpu_per_core    # CPU metrics (JSON)
├── memory_usage, memory_*     # Memory metrics
├── temperature, temperatures  # Thermal data
├── uptime, load_*             # System metrics
└── processes_*                # Process counts
```

---

## 🔧 Database Configuration

### Part I (SQLite)

```python
# server/app/config.py
DATABASE_URL = "sqlite:///./aetheredge.db"
```

### Part II (PostgreSQL)

```python
# Planned for Part II
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/aetheredge"
```

---

## 📈 Index Strategy

### Important Indexes

```sql
-- Fast node lookups by node_id
CREATE INDEX idx_nodes_node_id ON nodes(node_id);

-- Status-based filtering
CREATE INDEX idx_nodes_status ON nodes(status);

-- Time-series queries for telemetry
CREATE INDEX idx_telemetry_node_id ON telemetry(node_id);
CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp);

-- Combined index for dashboard queries
CREATE INDEX idx_telemetry_node_time ON telemetry(node_id, timestamp DESC);
```

---

## ⚡ Performance Considerations

### Part I Optimization

1. **Single file**: No network latency
2. **WAL mode**: Better concurrency for reads
3. **Batch inserts**: Group telemetry inserts

### Part II Scaling

1. **Partitioning**: Time-series partitioning for telemetry
2. **Read replicas**: Separate dashboard queries
3. **Connection pooling**: Efficient connection reuse
4. **Query caching**: Frequently accessed node data

---

## 🔄 Migration Path

### SQLite → PostgreSQL

1. **Export**: `sqlite3 aetheredge.db ".dump" > dump.sql`
2. **Transform**: Remove SQLite-specific syntax
3. **Import**: `psql aetheredge < dump.sql`

### Alembic Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

---

## 🧪 Database Testing

### Unit Tests

```python
def test_node_creation():
    # Create node
    node = await create_node(db, NodeRegister(...))
    assert node.node_id == "test-node"

def test_telemetry_ingestion():
    # Insert telemetry
    tel = await add_telemetry(db, TelemetryCreate(...))
    assert tel.cpu_usage == 45.2
```

---

## 📚 References

- SQLAlchemy: https://www.sqlalchemy.org/
- SQLite WAL: https://www.sqlite.org/wal.html
- PostgreSQL Partitioning: https://www.postgresql.org/docs/current/ddl-partitioning.html

---

*Document generated: 2026-09-30*