from locust import HttpUser, task, between
import random


class RateLimiterUser(HttpUser):
    wait_time = between(0.001, 0.005)

    @task
    def protected_endpoint(self) -> None:
        user_id = str(random.randint(1, 100_000))
        headers = {'X-User-Id': user_id}
        self.client.get('/protected', headers=headers)
