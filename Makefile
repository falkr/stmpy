all:
	@echo "Specify a target."

docs:
	pdoc --html --overwrite --html-dir ./docs ./stmpy

pypi: docs
	sudo python2 setup.py register sdist upload

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

runtests:
	python3 -m unittest tests/unit/test_stmpy.py

runcoverage:
	coverage run -m unittest tests/unit/test_stmpy.py
	coverage report
