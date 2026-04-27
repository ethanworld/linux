#!/bin/bash

# 恢复换回接口
ip link set lo up
ip route show table all

