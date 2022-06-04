#!/bin/sh

BASEDIR=$(dirname "$0")

conky -c "${BASEDIR}/conky.conf"
