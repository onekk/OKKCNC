NAME = OKKCNC
SOURCES =	OKKCNC/*.py \
		OKKCNC/controllers/*.py \
		OKKCNC/lib/*.py \
		OKKCNC/lib/python_utils/*.py \
		OKKCNC/lib/stl/*.py \
		OKKCNC/lib/svg/*.py \
		OKKCNC/lib/svg/path/*.py \

.PHONY = help

help:
	@echo see source

pot: OKKCNC/${NAME}.pot

OKKCNC/${NAME}.pot: ${SOURCES}
	xgettext --from-code=UTF-8 --keyword=N_ -d ${NAME} -o $@ $^

tags:
	ctags OKKCNC/*.py OKKCNC/lib/*.py OKKCNC/plugins/*.py

clean:
	git clean -Xf
	rm -f OKKCNC/*.pyc OKKCNC/*.pyo
	rm -f OKKCNC/controllers/*.pyc OKKCNC/controllers/*.pyo
	rm -f OKKCNC/lib/*.pyc OKKCNC/lib/*.pyo
	rm -f OKKCNC/lib/python_utils/*.pyc OKKCNC/lib/python_utils/*.pyo
	rm -f OKKCNC/lib/stl/*.pyc OKKCNC/lib/stl/*.pyo
	rm -f OKKCNC/lib/svg/*.pyc OKKCNC/lib/svg/*.pyo
	rm -f OKKCNC/lib/svg/path/*.pyc OKKCNC/lib/svg/path/*.pyo
	rm -f OKKCNC/plugins/*.pyc OKKCNC/plugins/*.pyo
