NOSETESTARGS = --with-doctest --doctest-tests

test: test2 test3

test2:
	nosetests $(NOSETESTARGS)

test3:
	nosetests3 $(NOSETESTARGS)

clean:
	rm -fr *~ */*~ */*.pyc */*.pyo gitexpy/__pycache__
