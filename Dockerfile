FROM python:3.12-slim AS builder

RUN pip install camoufox py-cord recognizer==1.4

RUN apt-get update && apt-get install -y --no-install-recommends libgtk-3-0 libx11-xcb1 libasound2 libgl1 xvfb xauth && rm -rf /var/lib/apt/lists/*

COPY dummy.py .

RUN xvfb-run -a python -u dummy.py

COPY . .

CMD ["python3", "-u", "main.py"]
