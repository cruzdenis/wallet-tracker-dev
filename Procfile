web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 300 --max-requests 1000 --max-requests-jitter 50 --worker-class sync --worker-tmp-dir /dev/shm src.main:app
scheduler: python3 scheduler_worker.py

