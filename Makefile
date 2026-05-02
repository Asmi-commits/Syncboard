.PHONY: dev build up down test logs clean

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

test:
	docker compose run --rm backend pytest app/tests/ -v --cov=app --cov-report=term-missing

logs:
	docker compose logs -f

logs-backend:
	docker compose logs -f backend

clean:
	docker compose down -v
	docker system prune -f
