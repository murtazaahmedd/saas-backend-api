.PHONY: install up test migrate run
install:
	pip install -r requirements.txt
up:                 ## Postgres + API on http://localhost:8000/docs
	docker compose up --build
migrate:
	python -m db.udf_load
run:
	uvicorn app.main:app_from_env --factory --reload
test:               ## needs a Postgres; set TEST_ADMIN_DSN (default: local socket in /tmp)
	python -m pytest -q
