#!/bin/bash

mount -t debugfs none /sys/kernel/debug
# 关闭跟踪
echo 0 > /sys/kernel/debug/tracing/tracing_on
echo nop > /sys/kernel/debug/tracing/current_tracer
echo "" > /sys/kernel/debug/tracing/trace

# 例如：打开函数流跟踪
echo function_graph > /sys/kernel/debug/tracing/current_tracer
echo do_sys_open > /sys/kernel/debug/tracing/set_graph_function
echo 1 > /sys/kernel/debug/tracing/tracing_on

# 执行命令
"$@"


# 关闭跟踪
echo 0 > /sys/kernel/debug/tracing/tracing_on