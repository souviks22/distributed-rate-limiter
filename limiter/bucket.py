from datetime import datetime, timezone
from log.logger import logger

class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity: int = capacity
        self.refilled: float = capacity
        self.tokens: float = 0
        self.refill_rate: float = refill_rate  # tokens per second
        self.last_refill: datetime = datetime.now(timezone.utc)

    def refill(self) -> None:
        now: datetime = datetime.now(timezone.utc)
        elapsed: float = (now - self.last_refill).total_seconds()
        added_tokens: float = elapsed * self.refill_rate
        self.refilled += added_tokens
        self.refilled = min(self.tokens + self.capacity, self.refilled)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        self.refill()
        # logger.info('Refilled: %f, Tokens: %f', self.refilled, self.tokens)
        if self.refilled - self.tokens >= tokens:
            self.tokens += tokens
            return True
        return False

    def merge(self, other: 'TokenBucket') -> None:
        """Merge with another bucket (CRDT merge)."""
        self.tokens = max(self.tokens, other.tokens)
        self.last_refill = max(self.last_refill, other.last_refill)
