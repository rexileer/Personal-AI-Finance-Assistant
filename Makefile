.PHONY: build up down logs migrate createsuperuser init-dev test lint format

build:
	docker compose build

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec web python manage.py migrate

createsuperuser:
	docker compose exec web python manage.py createsuperuser

init-dev:
	docker compose exec web python manage.py init_dev

test:
	docker compose exec web pytest -q

lint:
	docker compose exec web ruff check .

format:
	docker compose exec web ruff format .
