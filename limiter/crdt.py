from aiokafka import AIOKafkaProducer, AIOKafkaConsumer, TopicPartition
from limiter.bucket import CRDTBucket
from limiter.hashring import ConsistentHashRing
from redis import Redis
from utils.performance import sync_latency
from utils.logger import logger_of
import asyncio
import json

logger = logger_of(__name__)
HEARTBEAT_INTERVAL_SECONDS = 1
PEERS_RESOLUTION_SECONDS = 2
HEARTBEAT_TTL_SECONDS = 6

class CRDTNode:
    def __init__(self, node_id: str, producer: AIOKafkaProducer, consumer: AIOKafkaConsumer, store: Redis, capacity: int, refill_rate: float) -> None:
        self.id = node_id
        logger.info(self.id)
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.producer = producer
        self.consumer = consumer
        self.store = store
        self.hashring = ConsistentHashRing(self.id)
        self.buckets: dict[str, CRDTBucket] = {}
        self.peers: set[str] = set()
        self.delta: set[str] = set()

    async def start(self) -> None:
        await self.consumer.start()
        await self.producer.start()
        asyncio.create_task(self.send_heartbeat())
        asyncio.create_task(self.update_consumer_topics())
        asyncio.create_task(self.publish_messages())
        asyncio.create_task(self.consume_messages())

    async def stop(self) -> None:
        await self.producer.stop()
        await self.consumer.stop()

    async def send_heartbeat(self) -> None:
        while True:
            self.store.set(f'heartbeat:{self.id}', 'alive', ex=HEARTBEAT_TTL_SECONDS)
            await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
    
    async def update_consumer_topics(self) -> None:
        while True:
            active_nodes = [str(key).split(':', 1)[1] for key in self.store.scan_iter(match='heartbeat:*')]
            current_peers = self.hashring.get_peers(active_nodes)
            removed, added = self.peers - current_peers, current_peers - self.peers
            if removed or added:
                logger.info(current_peers)
                self.peers = current_peers
                partitions = [TopicPartition(f'crdt-node-{peer}', 0) for peer in self.peers]
                await self.consumer._client.force_metadata_update()
                self.consumer.assign(partitions)
            await asyncio.sleep(PEERS_RESOLUTION_SECONDS)

    async def consume_messages(self) -> None:
        async for msg in self.consumer:
            payload: dict = json.loads(msg.value)
            logger.info('consumer')
            logger.info(payload)
            user_id: str = payload['user_id']
            bucket: dict[str, float] = payload['bucket']
            incoming_bucket = CRDTBucket.deserialize(bucket, self.capacity, self.refill_rate)
            if user_id not in self.buckets:
                self.buckets[user_id] = incoming_bucket
            else:
                self.buckets[user_id].merge(incoming_bucket)
            sync_latency.add_from(incoming_bucket.last_refill)

    def get_bucket(self, user_id: str) -> CRDTBucket:
        if user_id not in self.buckets:
            self.buckets[user_id] = CRDTBucket(self.capacity, self.refill_rate)
        return self.buckets[user_id]
    
    def send_update(self, user_id: str) -> None:
        self.delta.add(user_id)

    async def publish_messages(self) -> None:
        while True:
            users = list(self.delta)
            self.delta.clear()
            for user_id in users:
                bucket = self.buckets[user_id]
                message = {
                    'user_id': user_id,
                    'bucket': bucket.serialize()
                }
                logger.info('producer')
                logger.info(message)
                await self.producer.send(f'crdt-node-{self.id}', json.dumps(message).encode())
            await asyncio.sleep(0.1)
