#!/bin/sh
set -eu

exe="python3.5 ../../router.pyc"
exe="../../router.py"

for i in $(seq 1 6) ; do
    tmux split-pane -v python3 ./router.py --addr "127.0.1.1" --update-period "10" --startup-commands "6.txt" &
    tmux select-layout even-vertical
done




# python3 ./router.py --addr "127.0.1.2" --update-period "10" --startup-commands "2.txt"
# python3 ./router.py --addr "127.0.1.3" --update-period "10" --startup-commands "3.txt"
# python3 ./router.py --addr "127.0.1.4" --update-period "10" --startup-commands "4.txt"
# python3 ./router.py --addr "127.0.1.5" --update-period "10" --startup-commands "5.txt"
# 