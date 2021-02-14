all:
	@echo "Specify a target."

docs:
	pdoc3 --html --force --output-dir ./docs ./stmpy

pypi: docs
	sudo python2 setup.py register sdist upload

code:
	python3 -m isort ./
	python3 -m black .

dev-install: docs
	rm -rf ./dist
	python3 setup.py sdist
	pip3 install -U dist/*.tar.gz

deploy: docs
	rm -rf ./dist
	python setup.py sdist
	twine upload dist/*

pep8:
	pep8-python2 pdoc/__init__.py scripts/pdoc

push:
	git push origin master
	git push github master

tests:
	python3 -m pytest -s tests/unit/test_stmpy.py

coverage:
	coverage run -m unittest tests/unit/test_stmpy.py
	coverage report
