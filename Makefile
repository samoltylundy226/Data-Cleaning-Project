.PHONY: help install download verify test clean

help:
	@echo "Available commands:"
	@echo "  make install       - Install required Python dependencies"
	@echo "  make download      - Download raw Chicago Food Inspections dataset"
	@echo "  make verify        - Verify dataset loading with Python"
	@echo "  make test          - Run pytest test suite"
	@echo "  make clean         - Clean temporary cache files"

install:
	pip install -r requirements.txt

verify:
	python verify_setup.py

test:
	pytest tests/

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
