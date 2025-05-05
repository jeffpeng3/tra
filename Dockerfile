FROM python:3.12-slim AS builder

RUN sudo apt install -y libgtk-3-0 libx11-xcb1 libasound2

RUN pip install camoufox py-cord

COPY dummy.py .

RUN python -u dummy.py

COPY . .

CMD ["python3", "-u", "main.py"]