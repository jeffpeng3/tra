FROM python:3.12-slim AS builder

RUN pip install patchright py-cord

RUN patchright install chromium

RUN patchright install-deps

COPY . .

CMD ["python3", "-u", "main.py"]