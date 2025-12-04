import argparse


def init():
    print("Initialize project")


def add_user():
    print("Add a new user")


parser = argparse.ArgumentParser(description="My Note RAG Tool")
subparsers = parser.add_subparsers(dest="command")

# 子命令
subparsers.add_parser("init", help="Initialize project")
subparsers.add_parser("add-user", help="Add a new user")

args = parser.parse_args()

# 根据子命令调用不同函数
if args.command == "init":
    init()
elif args.command == "add-user":
    add_user()
else:
    parser.print_help()
