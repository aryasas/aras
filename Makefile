docker-up:
	docker compose up -d --build

docker-test:
	DOCKER_E2E=1 pytest tests/e2e/test_docker_saas_flow.py -v

docker-down:
	docker compose down -v
