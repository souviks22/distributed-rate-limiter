from limiter.kafka_sync import KafkaSync


class DistributedRateLimiter:
    def __init__(self, kafka_sync: KafkaSync) -> None:
        self.kafka_sync: KafkaSync = kafka_sync

    async def start(self) -> None:
        await self.kafka_sync.start()

    async def stop(self) -> None:
        await self.kafka_sync.stop()

    async def allow_request(self, user_id: str) -> bool:
        bucket = self.kafka_sync.get_bucket(user_id)
        allowed: bool = bucket.consume()
        if allowed:
            await self.kafka_sync.publish_update(user_id)
        return allowed
