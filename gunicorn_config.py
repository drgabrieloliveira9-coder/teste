import os
import multiprocessing

bind = "0.0.0.0:" + str(os.getenv("PORT", "10000"))

workers = 2
worker_class = "sync"
worker_connections = 100
max_requests = 500
max_requests_jitter = 50

timeout = 120
graceful_timeout = 30
keepalive = 2

preload_app = True

accesslog = "-"
errorlog = "-"
loglevel = "info"

worker_tmp_dir = "/dev/shm"
