CBFLIB=/lmb/home/harry/CBFlib/CBFlib-0.9.5/lib
CBFINC=/lmb/home/harry/CBFlib/CBFlib-0.9.5/include
HDF5LIB=/lmb/home/harry/CBFlib/CBFlib-0.9.5/lib
CC=/usr/bin/gcc -O3
all:	
	${CC} -std=c99 -o minicbf -g \
	-I${CBFINC} \
	-L${CBFLIB} -Ilz4 \
	eiger2cbf.c \
	lz4/lz4.c lz4/h5zlz4.c \
	bitshuffle/bshuf_h5filter.c \
	bitshuffle/bshuf_h5plugin.c \
	bitshuffle/bitshuffle.c \
	${HDF5LIB}/libhdf5_hl.a \
	${HDF5LIB}/libhdf5.a \
	-lcbf -lm -lpthread -lz -ldl

clean: 
	rm -f *.o minicbf
