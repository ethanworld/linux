#!/bin/bash

mount -t debugfs none /sys/kernel/debug
# 关闭跟踪
echo 0 > /sys/kernel/debug/tracing/tracing_on
echo nop > /sys/kernel/debug/tracing/current_tracer
echo "" > /sys/kernel/debug/tracing/trace

# 例如：打开函数流跟踪
echo function_graph > /sys/kernel/debug/tracing/current_tracer
# 白名单
echo __sys_socket > /sys/kernel/debug/tracing/set_graph_function
echo __sys_connect >> /sys/kernel/debug/tracing/set_graph_function
echo __sys_bind >> /sys/kernel/debug/tracing/set_graph_function
echo __sys_listen >> /sys/kernel/debug/tracing/set_graph_function
echo __sys_accept4 >> /sys/kernel/debug/tracing/set_graph_function
echo input_event >> /sys/kernel/debug/tracing/set_graph_function

# 黑名单
echo do_interrupt_handler > /sys/kernel/debug/tracing/set_ftrace_notrace
echo cpu_have_feature >> /sys/kernel/debug/tracing/set_ftrace_notrace
echo handle_irq_desc >> /sys/kernel/debug/tracing/set_ftrace_notrace
echo irq_exit_rcu >> /sys/kernel/debug/tracing/set_ftrace_notrace
echo preempt_schedule_irq >> /sys/kernel/debug/tracing/set_ftrace_notrace
echo folios_put_refs >> /sys/kernel/debug/tracing/set_ftrace_notrace
echo free_unref_folios >> /sys/kernel/debug/tracing/set_ftrace_notrace
echo release_pages >> /sys/kernel/debug/tracing/set_ftrace_notrace

# $$ 代表当前 Shell 进程的 PID，ftrace 就只会记录命令（及其子进程）产生的内核调用
echo $$ > set_ftrace_pid
echo 1 > /sys/kernel/debug/tracing/tracing_on

# 执行命令
"$@"


# 关闭跟踪
echo 0 > /sys/kernel/debug/tracing/tracing_on

cat /sys/kernel/debug/tracing/trace > /coding/cat_proc_cpuinfo