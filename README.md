# Distributed Rate Limiter (CRDT + Token Bucket + Kafka)

A **production-grade**, **eventually consistent**, **decentralized rate limiter** built using the **Token Bucket algorithm** with **Commutative CRDTs** and **Apache Kafka** for synchronization.  
Designed to scale horizontally for **millions of users** and protect services without single points of failure.

---

## 📜 Table of Contents
- [Background](#-background)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
- [Stress Testing](#-stress-testing)
- [How it Works](#-how-it-works-detailed)
- [CRDT Merge Logic](#-crdt-merge-logic)
- [Improvements and Future Work](#-improvements-and-future-work)
- [License](#-license)

---

## 📚 Background

Typical rate limiters require centralized databases (Redis, etc.).  
But **centralized designs** fail to scale horizontally without becoming bottlenecks.

This project solves that using:
- **Token Bucket Algorithm**: classic rate-limiting mechanism.
- **CRDTs**: Conflict-Free Replicated Data Types allow concurrent updates without conflicts.
- **Kafka (KRaft Mode)**: decentralized message broker for state synchronization.

> **Goal**: Design a fast, scalable rate limiter that can handle millions of users **across multiple servers**.

---

## 🏗 Architecture

```plaintext
                +----------------+
                | Kafka (KRaft)   |
                +----------------+
                    ↑        ↑
                    |        |
      +-------------+        +--------------+
      |                                    |
+------------+                    +---------------+
| Server A   |                    | Server B      |
| Local bucket|                    | Local bucket  |
+------------+                    +---------------+
   ↑  ↓                                    ↑  ↓
Request Handling                    Request Handling
Token consumption                  Token consumption
Local Decision                      Local Decision
```

- Each server maintains its **own local buckets**.
- **Kafka** is used to **publish and sync bucket updates**.
- Each server **consumes** updates asynchronously and **merges** using **CRDT rules**.

---

## ✨ Features

- 🧠 **Decentralized**, **Eventually Consistent**.
- 🚀 **Low Latency**: Immediate local decision without waiting for Kafka.
- 🔄 **Self-Healing**: Automatic state correction via CRDT merging.
- ⚙️ **Highly Scalable**: Designed for millions of users.
- 📊 **429 Handling**: Proper rejection when rate limit exceeds.
- 🧪 **Stress Testing** ready using **Locust**.

---

## 🛠 Tech Stack

| Layer           | Technology         |
|:----------------|:-------------------|
| Language        | Python 3.11+         |
| API Server      | FastAPI             |
| Messaging Bus   | Apache Kafka (Bitnami Kafka, KRaft mode) |
| Async Consumer  | aiokafka            |
| Stress Testing  | Locust.io           |
| Dockerized Infra| Docker Compose      |

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/distributed-rate-limiter.git
cd distributed-rate-limiter
```

---

### 2. Install Docker

- Easiest way to proceed is by downloading [Docker Desktop](https://docs.docker.com/desktop/setup/install/mac-install/) straight away (recommended).

- You can install **Docker Engine** separately but that's up yo you.

---

### 3. Start Kafka (in KRaft mode)

We are using **Bitnami's lightweight Kafka** (no Zookeeper).

Start the cluster:

```bash
docker-compose up -d kafka
```

This spins up:
- Kafka server (port 9092)
- Schema registry if needed later (optional)

---

### 4. Start the Rate Limiter Service

Run the FastAPI server:

```bash
docker compose up -d rate_limiter
```

It will deploy 5 replicas of your Rate Limiter API in a containerized environment.

---

## 🔥 Stress Testing

We use **Locust** to simulate heavy load!

1. Run the Locust Master UI:

```bash
docker compose up -d master_locust
```

2. Run the Locust Workers:

```bash
docker compose up -d worker_locust
```

3. Open browser:

👉 http://localhost:8089

4. Configure:
- Number of users: `10000`
- Spawn rate: `500`
- Host: `http://rate_limiter:8000`
- Start!

Locust will simulate **millions of users** hammering the `/protected` API.

You will see **latency**, **success rate**, **failure rate**, etc.

---

## ⚙ How it Works (Detailed)

- Each user gets their own **TokenBucketState**.
- Servers consume **Kafka messages** of updated states.
- Each server maintains a **local copy** of user's bucket.
- On API call:
  - Check + Consume token locally.
  - Publish the update to Kafka.
- Kafka consumers receive updates → **merge buckets**.
- CRDT logic ensures eventual **conflict-free synchronization**.
- No central DB required.

---

## 🧠 CRDT Merge Logic

**Merge two buckets** by:
- Taking **minimum tokens left**.
- Taking **maximum last refill timestamp**.

```python
merged_tokens = min(local.tokens, incoming.tokens)
merged_last_refill = max(local.last_refill, incoming.last_refill)
```

✅ Ensures no over-counting of tokens.

✅ Allows concurrent updates.

✅ Self-healing.

---

## 📈 Improvements and Future Work

- [ ] **Snapshot buckets** periodically to avoid infinite Kafka replays.
- [ ] **Compaction topic** to retain only latest state per user.
- [ ] **Partition Kafka** by user ID for sharded scaling.
- [ ] **Advanced CRDTs** like PN-Counters for better deltas.
- [ ] **Rate limit per endpoint** instead of per user.
- [ ] **Prometheus + Grafana** for monitoring (easy to add).
- [ ] **Zero-Downtime Refill Service** (like cron job).

---

## 📄 License

This project is open-sourced under the **MIT License**.

---
