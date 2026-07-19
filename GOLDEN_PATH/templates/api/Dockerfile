FROM python:3.12-slim AS base
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*   # 安全基线
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd -m app && chown -R app /app                                   # 非 root 运行
USER app
EXPOSE 8000
HEALTHCHECK --interval=2m --timeout=10s CMD python3 -c "import urllib.request;urllib.request.urlopen('http://127.0.0.1:8000/healthz')"
CMD ["python3","-m","uvicorn","main:app","--host","0.0.0.0","--port","8000"]
