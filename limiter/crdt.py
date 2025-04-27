from datetime import datetime, timezone
from limiter.bucket import TokenBucket


class CRDTBucket:
    def __init__(self, bucket: TokenBucket) -> None:
        self.bucket: TokenBucket = bucket

    def merge(self, other: 'CRDTBucket') -> None:
        self.bucket.merge(other.bucket)

    def serialize(self) -> dict[str, float]:
        return {
            'tokens': self.bucket.tokens,
            'timestamp': self.bucket.last_refill.timestamp()
        }

    @staticmethod
    def deserialize(data: dict[str, float], capacity: int, refill_rate: float) -> 'CRDTBucket':
        bucket = TokenBucket(capacity, refill_rate)
        bucket.tokens = data['tokens']
        bucket.last_refill = datetime.fromtimestamp(data['timestamp'], tz=timezone.utc)
        return CRDTBucket(bucket)
