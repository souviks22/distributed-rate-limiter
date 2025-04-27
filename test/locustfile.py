from locust import HttpUser, task, between
import random


class RateLimiterUser(HttpUser):
    wait_time = between(0.001, 0.005)  # Tiny wait between requests (~1-5ms)

    @task
    def protected_endpoint(self) -> None:
        user_id = str(random.randint(1, 1_000_000))  # Simulate millions of users
        headers = {'X-User-Id': user_id}
        self.client.get('/protected', headers=headers)
