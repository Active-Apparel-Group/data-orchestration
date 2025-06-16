
.PHONY: build up down clean rebuild

build:
	docker compose build --no-cache kestra

up:
	docker compose up -d

down:
	docker compose down

clean:
	docker compose down -v
	docker system prune -f

rebuild: down build up