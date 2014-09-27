#! /usr/bin/make 

default:
	python setup.py check build

.PHONY: dist clean test_code test_py test

dist:
	python setup.py sdist

clean:
	python setup.py clean
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg*/
	rm -rf __pycache__/
	rm -f MANIFEST
	rm -rf docs/_*/
	rm -f nosetests.xml

test_code: clean
	flake8 bart/*.py

test_py:
	echo 'write tests'

test: test_code test_py
