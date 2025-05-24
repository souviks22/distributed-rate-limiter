from datetime import datetime, timezone

class Latency:
    def __init__(self) -> None:
        self.value = 0.0
        self.count = 0

    def add_from(self, date_time: datetime) -> None:
        latency = (datetime.now(timezone.utc) - date_time).total_seconds()
        self.value = (self.value * self.count + latency) / (self.count + 1)
        self.count += 1

    def average(self) -> float:
        return self.value
    