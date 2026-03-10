#!/bin/bash

alembic upgrade head
python3 /app/create_model.py
gunicorn server.main:app \
--workers 4 \
--worker-class uvicorn.workers.UvicornWorker \
--bind 0.0.0.0:8001 \
--log-level debug \
--access-logfile - \
--error-logfile -