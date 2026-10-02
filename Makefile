.PHONY: help install verify pipeline report test clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install required Python dependencies"
	@echo "  make pipeline      - Run end-to-end data quality pipeline"
	@echo "  make report        - Generate before vs after quality comparison report"
	@echo "  make test          - Run pytest test suite"
	@echo "  make verify        - Verify environment setup and raw data"
	@echo "  make clean         - Clean temporary cache files"

install:
	pip install -r requirements.txt

pipeline:
	python -m src.pipeline

report:
	python -m src.quality_report

verify:
	python verify_setup.py

test:
	pytest tests/

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
