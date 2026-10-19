"""命令行入口。

用法示例：
    python cli.py analyze "我的手机号是 13800138000"
    python cli.py analyze --file examples/sample.txt
    python cli.py analyze --file examples/sample.txt --json
    python cli.py mask --file examples/access.log --strategy mask
    python cli.py mask --file examples/access.log --strategy mask -o masked.log
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata
from pathlib import Path

from privmask import Anonymizer, Engine, summarize
from privmask.anonymizer import split_segments


def _prepare_stdout() -> None:
    """让中文在 CMD、PowerShell、Git Bash 里都能正常显示。

    坑在这里：Windows CMD 默认代码页是 GBK(936)，Python 会跟随用 GBK 输出，
    中文本来就正常。如果强行改成 UTF-8，反而会在 CMD 里变成乱码。
    所以只有在编码是 ascii（必然报 UnicodeEncodeError）时才切换。
    需要强制 UTF-8（比如输出重定向给别的程序）时，设环境变量 PRIVMASK_UTF8=1。
    """
    force = os.environ.get("PRIVMASK_UTF8") == "1"

    for stream in (sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", "") or "").lower().replace("-", "")
        if not force and encoding not in ("ascii", ""):
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


def _display_width(text: str) -> int:
    """中文占两格宽，直接用 ljust 会让表格错位。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


def _pad(text: str, width: int) -> str:
    return text + " " * max(width - _display_width(text), 0)


def _load_text(args: argparse.Namespace) -> str:
    if args.file:
        if not args.file.exists():
            raise SystemExit(f"文件不存在：{args.file}")
        return args.file.read_text(encoding="utf-8")
    if args.text:
        return args.text
    return sys.stdin.read()


def _cmd_analyze(args: argparse.Namespace) -> int:
    text = _load_text(args)
    entities = Engine().analyze(text)

    if args.json:
        payload = {
            "count": len(entities),
            "summary": summarize(entities),
            "entities": [e.to_dict() for e in entities],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not entities:
        print("未发现敏感信息。")
        return 0

    print(f"共发现 {len(entities)} 处敏感信息：\n")
    print(f"  {_pad('类型', 14)}{_pad('内容', 26)}位置")
    print(f"  {'-' * 14}{'-' * 26}{'-' * 16}")
    for entity in entities:
        print(
            f"  {_pad(entity.entity_type, 14)}"
            f"{_pad(entity.text, 26)}"
            f"[{entity.start}, {entity.end})"
        )

    print("\n按类型统计：")
    for entity_type, count in summarize(entities).items():
        print(f"  {entity_type:<12}{count}")
    return 0


def _cmd_mask(args: argparse.Namespace) -> int:
    text = _load_text(args)
    entities = Engine().analyze(text)
    masked = Anonymizer(strategy=args.strategy).anonymize(text, entities)

    if args.output:
        args.output.write_text(masked, encoding="utf-8")
        print(f"已写入 {args.output}（共处理 {len(entities)} 处）")
        return 0

    if args.show_segments:
        for chunk, entity in split_segments(text, entities):
            if entity is None:
                print(chunk, end="")
            else:
                print(f"[[{entity.entity_type}:{chunk}]]", end="")
        print()
        return 0

    print(masked, end="" if masked.endswith("\n") else "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="privmask",
        description="中文敏感信息识别与脱敏工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="只识别，输出命中结果")
    p_analyze.add_argument("text", nargs="?", help="直接传入要分析的文本")
    p_analyze.add_argument("--file", "-f", type=Path, help="从文件读取")
    p_analyze.add_argument("--json", action="store_true", help="以 JSON 输出")
    p_analyze.set_defaults(func=_cmd_analyze)

    p_mask = sub.add_parser("mask", help="识别并脱敏")
    p_mask.add_argument("text", nargs="?", help="直接传入要处理的文本")
    p_mask.add_argument("--file", "-f", type=Path, help="从文件读取")
    p_mask.add_argument(
        "--strategy",
        "-s",
        default="mask",
        choices=Anonymizer.SUPPORTED_STRATEGIES,
        help="脱敏策略，默认 mask",
    )
    p_mask.add_argument("--output", "-o", type=Path, help="写入文件")
    p_mask.add_argument(
        "--show-segments",
        action="store_true",
        help="以 [[类型:内容]] 的形式标出敏感片段，便于肉眼检查",
    )
    p_mask.set_defaults(func=_cmd_mask)

    return parser


def main(argv: list[str] | None = None) -> int:
    _prepare_stdout()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
