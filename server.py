"""Web 服务入口。

启动方式：
    python server.py

然后浏览器打开 http://127.0.0.1:5000

接口：
    GET  /              返回前端页面
    POST /api/analyze   分析文本，返回命中结果 + 脱敏文本
    GET  /api/health    健康检查
"""

from __future__ import annotations

import logging
import os
import sys

from flask import Flask, jsonify, request

from privmask import Anonymizer, Engine, summarize
from privmask.anonymizer import split_segments

#: 单次请求的文本长度上限，防止被超长文本拖死
MAX_TEXT_LENGTH = 50_000

app = Flask(__name__, static_folder="web", static_url_path="/static")

# 引擎和识别器无状态，进程内复用一个实例即可
engine = Engine()

# 关掉 werkzeug 的逐请求日志，演示时终端看着干净
logging.getLogger("werkzeug").setLevel(logging.WARNING)


@app.get("/")
def index():
    return app.send_static_file("index.html")


@app.get("/api/health")
def api_health():
    return jsonify({"status": "ok"})


@app.post("/api/analyze")
def api_analyze():
    """分析文本。

    请求体：
        {"text": "待分析文本", "strategy": "mask"}

    响应体：
        count     命中数量
        summary   按类型统计
        segments  切好的片段，前端直接渲染高亮
        masked    按策略脱敏后的文本
        entities  完整实体列表（含位置和置信度）
    """
    payload = request.get_json(silent=True) or {}
    text = payload.get("text") or ""
    strategy = payload.get("strategy") or "mask"

    if not isinstance(text, str):
        return jsonify({"error": "text 必须是字符串"}), 400
    if len(text) > MAX_TEXT_LENGTH:
        return jsonify({"error": f"文本长度超过 {MAX_TEXT_LENGTH} 字符上限"}), 400
    if strategy not in Anonymizer.SUPPORTED_STRATEGIES:
        return jsonify({"error": f"不支持的策略：{strategy}"}), 400

    entities = engine.analyze(text)

    segments = [
        {"text": chunk, "type": entity.entity_type if entity else None}
        for chunk, entity in split_segments(text, entities)
    ]

    return jsonify(
        {
            "count": len(entities),
            "summary": summarize(entities),
            "segments": segments,
            "masked": Anonymizer(strategy=strategy).anonymize(text, entities),
            "entities": [entity.to_dict() for entity in entities],
        }
    )


def main() -> None:
    # 默认只监听本机，避免把演示服务暴露到局域网。
    # 容器里需要对外提供服务时，用环境变量改成 0.0.0.0。
    host = os.environ.get("PRIVMASK_HOST", "127.0.0.1")
    port = int(os.environ.get("PRIVMASK_PORT", "5000"))

    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])

    print("=" * 58)
    print("  privmask 已启动")
    print(f"  地址: http://{'127.0.0.1' if host == '0.0.0.0' else host}:{port}")
    print("  按 Ctrl+C 停止服务")
    print("=" * 58)

    # debug=False：演示时不要自动重载，否则改文件会反复重启
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
