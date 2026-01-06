FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md requirements.txt /app/
COPY aisubscalp /app/aisubscalp
COPY config /app/config
COPY examples /app/examples

RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir .

ENTRYPOINT ["aisubscalp"]
CMD ["scan"]
