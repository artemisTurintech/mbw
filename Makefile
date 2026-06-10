#CFLAGS=-O2 -Wall -g
NAME=mbw
TARFILE=${NAME}.tar.gz
CC    = C:/Users/turintech/scoop/apps/mingw/current/bin/gcc
SHELL = C:/Program Files/Git/bin/bash.exe

.PHONY: compile test benchmark

compile:
	$(CC) -O2 -o mbw mbw.c

test: compile
	./mbw -n 1 10 > /dev/null && echo "PASS: all-tests run"
	./mbw 2>&1 | grep -q "no array size" && echo "PASS: missing arg error"
	./mbw -n 1 0 2>&1 | grep -q "array size wrong" && echo "PASS: zero-size error"
	@echo "All tests passed."

benchmark:
	./mbw 1000

mbw: mbw.c
	$(CC) -O2 -o mbw mbw.c

clean:
	rm -f mbw
	rm -f ${NAME}.tar.gz

${TARFILE}: clean
	 tar cCzf .. ${NAME}.tar.gz --exclude-vcs ${NAME} || true

rpm: ${TARFILE}
	 rpmbuild -ta ${NAME}.tar.gz 
