from __future__ import annotations

import argparse
import json

from agent_audio.installer import doctor, perform_install, register_agents
from agent_audio.runtime import install_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Audio bootstrap")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--doctor", action="store_true")
    group.add_argument("--runtime-only", action="store_true")
    group.add_argument("--register-only", action="store_true")
    args = parser.parse_args()

    if args.doctor:
        result = doctor()
    elif args.runtime_only:
        result = {"runtime_backend": install_runtime(), "doctor": doctor()}
    elif args.register_only:
        result = register_agents()
    else:
        result = perform_install()

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
