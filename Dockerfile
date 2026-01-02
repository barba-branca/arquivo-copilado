FROM python:3.10-slim
RUN apt-get update && apt-get install -y x11vnc xvfb fluxbox wget && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . /app/
RUN pip install --no-cache-dir -r /app/requirements.txt
ENV PYTHONPATH=/app
CMD ["python3", "run_agent.py"]