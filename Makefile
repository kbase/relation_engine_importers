
install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install --extra-index-url https://pypi.anaconda.org/kbase/simple kbase-workspace-utils==0.0.12
	pip install -r dev-requirements.txt

test:
	flake8 --max-complexity 5 arangodb_biochem_importer
	mypy --ignore-missing-imports arangodb_biochem_importer
	python -m pyflakes arangodb_biochem_importer
	bandit -r arangodb_biochem_importer
	python -m unittest discover arangodb_biochem_importer/test
