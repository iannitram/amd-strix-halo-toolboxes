"""``python -m workstation``: serve | plan | update (CLI). Planned: #6 (serve), #24 (update)."""

import sys


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: python -m workstation {serve,plan,update} ...")
        return 0
    print(f"not built yet: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
