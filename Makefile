NOSETESTARGS = --with-doctest --doctest-tests
NOSECOVERARGS = --with-coverage --cover-inclusive --cover-package=gitexpy --cover-html

test: test2 test3

test2:
	nosetests $(NOSETESTARGS)

test3:
	nosetests3 $(NOSETESTARGS)

coverage: coverage2 coverage3

coverage2:
	nosetests $(NOSETESTARGS) $(NOSECOVERARGS) --cover-html-dir=cover2

coverage3:
	nosetests3 $(NOSETESTARGS) $(NOSECOVERARGS) --cover-html-dir=cover3

clean:
	rm -fr *~ */*~ */*.pyc */*.pyo gitexpy/__pycache__ cover2 cover3 .coverage
