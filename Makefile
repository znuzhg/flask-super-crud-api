.PHONY: format lint typecheck test run

format:
	black . && isort .

lint:
	ruff .

typecheck:
	mypy .

test:
	pytest -q

run:
	python app.py

