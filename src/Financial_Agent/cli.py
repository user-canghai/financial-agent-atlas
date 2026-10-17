from __future__ import annotations

import argparse

from Financial_Agent import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="基于 MCP 与 Skills 的金融领域 Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            '  uv run main.py --run "总结 2025 年中国经济形势，不超过 200 字"\n'
            "  uv run main.py --interactive\n"
            "  uv run main.py --check\n"
        ),
    )
    parser.add_argument("-r", "--run", type=str, metavar="PROMPT", help="运行单轮对话")
    parser.add_argument("-i", "--interactive", action="store_true", help="启动交互模式（多轮对话）")
    parser.add_argument(
        "-c",
        "--conversation",
        type=str,
        metavar="NAME",
        help="对话名称，用于隔离不同会话的历史记录",
    )
    parser.add_argument("--debug", action="store_true", help="显示节点执行情况（调试模式）")
    parser.add_argument("--check", action="store_true", help="检查依赖、目录与环境变量后退出")
    parser.add_argument("--mcp-status", action="store_true", help="查看 MCP 服务器配置与可执行性")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.check:
        from Financial_Agent.diagnostics import run_self_check

        return run_self_check()
    if args.mcp_status:
        from Financial_Agent.diagnostics import print_mcp_status

        return print_mcp_status()

    from Financial_Agent.repl.interactive import run_interactive_mode, run_single_chat

    conversation_name: str | None = args.conversation

    if args.run:
        run_single_chat(args.run, debug=args.debug, conversation_name=conversation_name)
    elif args.interactive:
        run_interactive_mode(debug=args.debug, conversation_name=conversation_name)
    else:
        print("=" * 60)
        print("运行默认单轮交互示例（你好）")
        if conversation_name:
            print(f"对话名称: {conversation_name}")
        print("=" * 60)
        run_single_chat("你好", debug=args.debug, conversation_name=conversation_name)
    return 0


__all__ = ["build_parser", "main"]
