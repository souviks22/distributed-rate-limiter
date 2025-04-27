from datetime import datetime, timezone


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity: int = capacity
        self.tokens: float = capacity
        self.refill_rate: float = refill_rate  # tokens per second
        self.last_refill: datetime = datetime.now(timezone.utc)

    def refill(self) -> None:
        now: datetime = datetime.now(timezone.utc)
        elapsed: float = (now - self.last_refill).total_seconds()
        added_tokens: float = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + added_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def merge(self, other: 'TokenBucket') -> None:
        """Merge with another bucket (CRDT merge)."""
        self.tokens = max(self.tokens, other.tokens)
        self.last_refill = max(self.last_refill, other.last_refill)
