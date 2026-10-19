# privmask 容器镜像
#
# 构建：
#   docker build -t privmask:0.1 .
# 运行：
#   docker run --rm -p 5000:5000 privmask:0.1
# 然后访问 http://127.0.0.1:5000

FROM python:3.13-slim

# 不生成 .pyc、日志直接输出到终端
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PRIVMASK_HOST=0.0.0.0 \
    PRIVMASK_PORT=5000

WORKDIR /app

# 先单独装依赖，改代码时不会让这一层缓存失效
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY privmask/ ./privmask/
COPY web/ ./web/
COPY server.py .
COPY cli.py .

# 用非 root 用户运行，容器被突破时影响范围更小
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/api/health')" || exit 1

CMD ["python", "server.py"]
