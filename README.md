# Distributed Rate Limiter (CRDT + Token Bucket + Kafka)

A **production-grade**, **eventually consistent**, **decentralized rate limiter** built using the **Token Bucket algorithm** with **Commutative CRDTs** and **Apache Kafka** for synchronization.  
Designed to scale horizontally for **millions of users** and protect services without single points of failure.

---

## 📜 Table of Contents
- [Background](#-background)
- [Architecture](#-architecture)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Getting Started](#-getting-started)
- [Running the Project](#-running-the-project)
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

## 🗂 Project Structure

```bash
├── README.md
├── docker-compose.yml
├── service
│   ├── app.py          # FastAPI server
│   ├── limiter.py      # Token Bucket + CRDT logic
│   ├── kafka_sync.py   # Kafka producer/consumer
│   ├── models.py       # Data models
├── stress_test
│   ├── locustfile.py   # Stress testing users
└── requirements.txt
```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/distributed-rate-limiter.git
cd distributed-rate-limiter
```

---

### 2. Install Dependencies

Create a virtual environment (optional but recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

Install all Python packages:

```bash
pip install -r requirements.txt
```

---

### 3. Start Kafka (in KRaft mode)

We are using **Bitnami's lightweight Kafka** (no Zookeeper).

Start the cluster:

```bash
docker-compose up -d
```

This spins up:
- Kafka server (port 9092)
- Schema registry if needed later (optional)

---

### 4. Start the Rate Limiter Service

Run the FastAPI server:

```bash
uvicorn service.app:app --host 0.0.0.0 --port 8000 --reload
```

Your API is now running at:

👉 http://localhost:8000/protected

---

## 🏎 Running the Project

Once everything is up:

- Call `POST http://localhost:8000/protected`
- Include a header:
  ```
  X-User-ID: <some-user-id>
  ```
- Server will:
  - Identify the user
  - Check their token bucket
  - Allow or reject based on available tokens
- If user exceeds allowed rate → returns **429 Too Many Requests**.

Example:

```bash
curl -X POST http://localhost:8000/protected -H "X-User-ID: 1234"
```

---

## 🔥 Stress Testing

We use **Locust** to simulate heavy load!

1. Install Locust:

```bash
pip install locust
```

2. Go to `stress_test/`:

```bash
cd stress_test
```

3. Run Locust:

```bash
locust -f locustfile.py --host=http://localhost:8000
```

4. Open browser:

👉 http://localhost:8089

5. Configure:
- Number of users: `10000`
- Spawn rate: `500`
- Host: `http://localhost:8000`
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

# 🚀 Final Words

This distributed rate limiter is designed for:
- Massive scale
- Fault-tolerance
- Near real-time consistency
- No single point of failure

**Perfect for your final year project and beyond!**

---

# 📌 Important Commands Summary

| Action | Command |
|:-------|:--------|
| Start Kafka | `docker-compose up -d` |
| Start API Server | `uvicorn service.app:app --host=0.0.0.0 --port=8000 --reload` |
| Start Stress Test | `locust -f stress_test/locustfile.py --host=http://localhost:8000` |
| Open Locust UI | `http://localhost:8089` |

---
