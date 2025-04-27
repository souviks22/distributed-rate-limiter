.PHONY: start kafka install test

install:
	pip3 install -r requirements.txt

start:
	python3 -m uvicorn service.app:app --host 0.0.0.0 --port 8000 --reload

kafka:
	docker-compose up -d

test:
	python3 -m locust -f test/locustfile.py --headless -u 10000 -r 500 --host=http://localhost:8000
