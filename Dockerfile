FROM python:3.13-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY pyproject.toml .
COPY main.py .
COPY aiModelStudy01/ ./aiModelStudy01/

# 环境变量（通过 docker-compose 或 K8s Secret 注入）
ENV ENVIRONMENT=production
ENV PYTHONPATH=/app

# 运行
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]