# gunicorn.conf.py

# Socket to bind
bind = 'unix:/home/nixos-server/Fun/Projects/myproject.sock'

# Number of worker processes
workers = 3

# The maximum number of requests a worker will process before restarting
max_requests = 1000

# Logging configuration
accesslog = '/home/nixos-server/Fun/Projects/logs/gunicorn-access.log'
errorlog = '/home/nixos-server/Fun/Projects/logs/gunicorn-error.log'
loglevel = 'info'

# Timeout settings
timeout = 30

# Daemonize the Gunicorn process (run in the background)
daemon = True
