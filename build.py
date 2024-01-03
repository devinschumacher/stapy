"""
Copyright (c) 2023, Magentix
This code is licensed under simplified BSD license (see LICENSE for details)
"""
import stapy
import sys


def main():
    envs = []
    for env in sys.argv[1:]:
        envs.append(env)
    stapy.build(envs)
    print('\nPress enter to exit')
    input()


if __name__ == "__main__":
    main()
