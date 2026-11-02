"""``python -m workstation``: local service; update CLI planned in #24."""

import argparse
import sys

from workstation.runtime.fake import FakeRuntime
from workstation.service.app import serve
from workstation.service.security import DEFAULT_ALLOWED_HOSTS


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help"):
        print("usage: python -m workstation {serve,plan,update} ...")
        return 0
    if argv[0] == "serve":
        parser = argparse.ArgumentParser(prog="python -m workstation serve")
        parser.add_argument("--fake", action="store_true", help="use the in-memory demo runtime")
        parser.add_argument("--host", default="127.0.0.1")
        parser.add_argument("--port", type=int, default=8765)
        parser.add_argument("--allow-lan", action="store_true",
                            help="explicitly permit a different bind address")
        parser.add_argument("--allowed-host", action="append", default=[],
                            help="additional accepted Host and Origin name (without port)")
        args = parser.parse_args(argv[1:])
        if not args.fake:
            parser.error("the real runtime is not built yet; use --fake")
        try:
            serve(host=args.host, port=args.port, runtime=FakeRuntime(),
                  allow_lan=args.allow_lan,
                  allowed_hosts=DEFAULT_ALLOWED_HOSTS | set(args.allowed_host))
        except (ValueError, OSError) as exc:
            parser.error(str(exc))
        return 0
    print(f"not built yet: {argv[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
