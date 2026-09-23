#!/bin/bash
# ============================================================
# FAST-LIO 内存监控（崩溃现场取证）
# ------------------------------------------------------------
# 背景：树莓派内存有限，FAST-LIO 体素地图无限累积会把内存吃满
#       然后抛 std::bad_alloc 崩溃。
# 教训：崩溃后再看 free -h 是没用的（进程已死，内存早已释放），
#       必须挂一个循环，持续记录，才能抓到崩溃瞬间。
#
# 用法: ./watch_mem.sh            # 默认 2 秒一次
#       ./watch_mem.sh 1 500      # 1 秒一次，最多 500 次
# ============================================================

INTERVAL=${1:-2}
MAX=${2:-0}          # 0 = 无限循环

i=0
while true; do
    date +%T
    free -h | grep Mem
    # 单独盯 FAST-LIO 进程（laserMapping）的常驻内存
    ps -o pid,rss,cmd -C laserMapping 2>/dev/null
    echo ---

    i=$((i+1))
    [ "$MAX" -gt 0 ] && [ "$i" -ge "$MAX" ] && break
    sleep "$INTERVAL"
done
