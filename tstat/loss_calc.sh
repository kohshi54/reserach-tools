#!/bin/bash

set -e

./retx_calc.sh log_tcp_nocomplete
./retx_calc.sh log_tcp_complete
./ooo_calc.sh log_tcp_nocomplete
./ooo_calc.sh log_tcp_complete

