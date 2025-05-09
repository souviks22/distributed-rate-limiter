class SyncLatency:

    def __init__(self) -> None:
        self.value: float = 0
        self.count: int = 0

    def add_latency(self, latency) -> None:
        self.value = (self.value * self.count + latency) / (self.count + 1)
        self.count += 1

    def get_latency(self) -> float:
        return self.value
    
sync_latency = SyncLatency()