#!/bin/bash
tmux new-session -d -s pa3
tmux set-option -t pa3 set-remain-on-exit on
tmux new-window -d -t pa3 -n main '/root/main.sh'