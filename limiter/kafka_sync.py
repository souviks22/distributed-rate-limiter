import asyncio
import json
import time
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from limiter.crdt import CRDTBucket
from limiter.bucket import TokenBucket
from log.logger import logger

class KafkaSync:
    def __init__(self, brokers: str, topic: str, capacity: int, refill_rate: float) -> None:
        self.topic: str = topic
        self.capacity: int = capacity
        self.refill_rate: float = refill_rate
        self.producer: AIOKafkaProducer = AIOKafkaProducer(bootstrap_servers=brokers)
        self.consumer: AIOKafkaConsumer = AIOKafkaConsumer(topic, bootstrap_servers=brokers, group_id=None)
        self.buckets: dict[str, CRDTBucket] = {}
        self.buffer: list[dict] = []

    async def start(self) -> None:
        await self.producer.start()
        await self.consumer.start()
        asyncio.create_task(self.consume_messages())
        asyncio.create_task(self.publish_messages())

    async def stop(self) -> None:
        await self.producer.stop()
        await self.consumer.stop()

    async def consume_messages(self) -> None:
        async for msg in self.consumer:
            payload: dict = json.loads(msg.value)
            user_id: str = payload['user_id']
            data: dict[str, float] = payload['bucket']

            incoming_bucket = CRDTBucket.deserialize(data, self.capacity, self.refill_rate)
            if user_id not in self.buckets:
                self.buckets[user_id] = incoming_bucket
            else:
                self.buckets[user_id].merge(incoming_bucket)
            
            # logger.info('CRDT sync latency: %f ms', (time.time() - payload['timestamp']) * 1000)

    async def publish_update(self, user_id: str) -> None:
        bucket = self.buckets[user_id]
        message: dict = {
            'user_id': user_id,
            'bucket': bucket.serialize(),
            'timestamp': time.time()
        }
        # logger.info('Published from this instance. Current Tokens: %f', bucket.bucket.tokens)
        self.buffer.append(message)

    async def publish_messages(self) -> None:
        while True:
            for message in self.buffer:
                await self.producer.send_and_wait(self.topic, json.dumps(message).encode())
            self.buffer.clear()
            # logger.info('Published after 200ms')
            await asyncio.sleep(0.2) # 200 ms batch window
            

    def get_bucket(self, user_id: str) -> TokenBucket:
        if user_id not in self.buckets:
            self.buckets[user_id] = CRDTBucket(TokenBucket(self.capacity, self.refill_rate))
        return self.buckets[user_id].bucket
