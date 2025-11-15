#!/usr/bin/env python3
"""Entry point for the MCP file server."""

import asyncio
import json
import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

from models import MCPMessage
from server import MCPFileServer

# ----------------------------------------------------------------------
# Basic logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP file server — performs sandboxed file operations with enhanced security."
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        default=None,
        help=("Working directory for the server. If omitted, the current "
              "process directory is used. Must exist and be readable/writable."),
    )
    return parser.parse_args()


async def main() -> None:
    """Main event loop — reads JSON‑RPC messages from stdin and writes responses to stdout."""
    args = parse_args()

    # Validate the supplied directory (if any)
    work_dir: Optional[Path] = None
    if args.directory is not None:
        if not args.directory.is_dir():
            logger.error(f"The specified directory does not exist or is not a folder: {args.directory}")
            sys.exit(1)
        work_dir = args.directory

    server = MCPFileServer(work_dir)

    # Simple line‑delimited JSON RPC protocol
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:          # EOF
                break

            line = line.strip()
            if not line:
                continue

            try:
                message_dict = json.loads(line)
                message = MCPMessage.from_dict(message_dict)
            except json.JSONDecodeError as exc:
                logger.error(f"Invalid JSON received: {exc}")
                continue

            response = await server.handle_message(message)

            if response:
                print(json.dumps(response.to_dict()), flush=True)

        except EOFError:
            break
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
            break
        except Exception as exc:
            logger.error(f"Unexpected error: {exc}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server terminated by keyboard interrupt")
    except Exception as exc:
        logger.error(f"Fatal error: {exc}")
        sys.exit(1)