#!/usr/bin/env python3
"""
Generic Hadoop Streaming REDUCER.
Usage: reducer.py sum   -> key \t total
       reducer.py avg   -> key \t average

Hadoop sorts mapper output by key, so all values for one key
arrive together.
"""
import sys


def emit(key, total, count, mode):
    if key is None:
        return
    if mode == "avg":
        print(f"{key}\t{total / count:.2f}")
    else:
        print(f"{key}\t{int(total) if total.is_integer() else round(total, 2)}")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "sum"
    current, total, count = None, 0.0, 0

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            key, value = line.split("\t", 1)
            value = float(value)
        except ValueError:
            continue
        if key == current:
            total += value
            count += 1
        else:
            emit(current, total, count, mode)
            current, total, count = key, value, 1

    emit(current, total, count, mode)


if __name__ == "__main__":
    main()
