from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic
from redis import Redis
from limiter.crdt import CRDTNode
import uuid
import asyncio

class DistributedRateLimiter:
    def __init__(self, brokers: str, store: str, capacity: int = 10, refill_rate: float = 1.0) -> None:
        self.id = str(uuid.uuid4())
        producer = AIOKafkaProducer(
            bootstrap_servers=brokers, 
            compression_type='lz4',
            max_batch_size=128*1024,
            linger_ms=100
        )
        consumer = AIOKafkaConsumer(bootstrap_servers=brokers)
        host, port = store.split(':', 1)
        store = Redis(host=host, port=port, decode_responses=True)
        self.admin = AIOKafkaAdminClient(bootstrap_servers=brokers)
        self.node = CRDTNode(
            node_id=self.id,
            producer=producer,
            consumer=consumer,
            store=store,
            capacity=capacity, 
            refill_rate=refill_rate
        )

    async def start(self) -> None:
        try:
            await self.create_node_topic()
            await self.node.start()
        except:
            pass

    async def stop(self) -> None:
        try:
            await self.node.stop()
        except:
            pass

    async def create_node_topic(self) -> None:
        try:
            await self.admin.start()
            topic = NewTopic(name=f'crdt-node-{self.id}', num_partitions=1, replication_factor=2)
            await self.admin.create_topics([topic])
            await asyncio.sleep(30)
        finally:
            await self.admin.close()

    def allow_request(self, user_id: str) -> bool:
        bucket = self.node.get_bucket(user_id)
        allowed = bucket.consume()
        if allowed:
            self.node.send_update(user_id)
        return allowed, self.id
