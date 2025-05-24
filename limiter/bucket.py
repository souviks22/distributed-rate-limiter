from datetime import datetime, timezone

class CRDTBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        # maximum available tokens at any time
        self.capacity = capacity
        # tokens to be added per second
        self.refill_rate = refill_rate
        # g-counter for used tokens at real time
        self.used_tokens = 0.0
        # g-counter for usable tokens upper bound
        self.usable_tokens = float(capacity)
        # latest timestamp of refill
        self.last_refill = datetime.now(tz=timezone.utc)

    def refill(self) -> None:
        now = datetime.now(tz=timezone.utc)
        elapsed_time = (now - self.last_refill).total_seconds()
        elapsed_tokens = elapsed_time * self.refill_rate
        self.usable_tokens += elapsed_tokens
        self.usable_tokens = min(self.used_tokens + self.capacity, self.usable_tokens)
        self.last_refill = now

    def consume(self) -> bool:
        self.refill()
        if self.usable_tokens - self.used_tokens >= 1:
            self.used_tokens += 1
            return True
        return False
    
    def merge(self, other: 'CRDTBucket') -> None:
        self.used_tokens = max(self.used_tokens, other.used_tokens)
        self.usable_tokens = max(self.usable_tokens, other.usable_tokens)
        self.last_refill = max(self.last_refill, other.last_refill)

    def serialize(self) -> dict[str, float]:
        return {
            'used_tokens': self.used_tokens,
            'usable_tokens': self.usable_tokens,
            'timestamp': self.last_refill.timestamp()
        }

    @staticmethod
    def deserialize(data: dict[str, float], capacity: int, refill_rate: float) -> 'CRDTBucket':
        bucket = CRDTBucket(capacity, refill_rate)
        bucket.used_tokens = data['used_tokens']
        bucket.usable_tokens = data['usable_tokens']
        bucket.last_refill = datetime.fromtimestamp(data['timestamp'], tz=timezone.utc)
        return bucket
