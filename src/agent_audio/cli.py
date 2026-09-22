from __future__ import annotations

import argparse
import json

from .installer import doctor, perform_install, register_agents
from .runtime import generate_audio, install_runtime


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-audio")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="Inspect hardware, agents and runtime readiness")
    sub.add_parser("install-runtime", help="Install the selected Stable Audio runtime")
    sub.add_parser("register", help="Register MCP + Skill with detected agents")

    install = sub.add_parser("install", help="Install runtime and register detected agents")
    install.add_argument("--no-runtime", action="store_true")
    install.add_argument("--no-register", action="store_true")

    generate = sub.add_parser("generate", help="Generate a WAV from a text prompt")
    generate.add_argument("prompt")
    generate.add_argument("--seconds", type=float, default=10.0)
    generate.add_argument("--out", default=None)
    generate.add_argument("--negative-prompt", default=None)

    args = parser.parse_args()
    if args.command == "doctor":
        result = doctor()
    elif args.command == "install-runtime":
        result = {"runtime_backend": install_runtime()}
    elif args.command == "register":
        result = register_agents()
    elif args.command == "install":
        result = perform_install(runtime=not args.no_runtime, register=not args.no_register)
    else:
        result = {
            "output": str(
                generate_audio(
                    args.prompt,
                    seconds=args.seconds,
                    output_path=args.out,
                    negative_prompt=args.negative_prompt,
                )
            )
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
