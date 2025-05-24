import hashlib
import bisect
from utils.logger import logger_of

logger = logger_of(__name__)
MAX_PEERS = 5

class ConsistentHashRing:
    def __init__(self, invoking_node_id: str) -> None:
        self.ring: list[tuple[int, str]] = []
        self.node = invoking_node_id
    
    def hash(self, node_id: str) -> int:
        return int(hashlib.md5(node_id.encode()).hexdigest(), 16) % (10**9+7)
    
    def get_peers(self, active_nodes: list[str]) -> set[str]:
        self.ring = sorted((self.hash(node), node) for node in active_nodes)
        index = bisect.bisect_right(self.ring, (self.hash(self.node), self.node))
        peers = []
        for _ in range(min(MAX_PEERS, len(self.ring) - 1)):
            index %= len(self.ring)
            peers.append(self.ring[index][1])
            index += 1
        return set(peers)
            