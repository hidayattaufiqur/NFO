import os
import multiprocessing

# Socket to bind bind = 'unix:/home/nixos-server/Fun/Projects/myproject.sock'

'''
configurations below follow Google Cloud documentation
[https://cloud.google.com/appengine/docs/flexible/python/runtime#recommended_gunicorn_configuration]
'''

# workers = multiprocessing.cpu_count() * 2 + 1
worker = 1
forwarded_allow_ips = '*'
secure_scheme_headers = {'X-FORWARDED-PROTO': 'https'}

timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
bind = os.environ.get('GUNICORN_BIND', '0.0.0.0:5000')

# The maximum number of requests a worker will process before restarting
max_requests = 1000

# Logging configuration
accesslog = '/home/nixos-server/Fun/Projects/ontology-BE/logs/gunicorn-access.log'
errorlog = '/home/nixos-server/Fun/Projects/ontology-BE/logs/gunicorn-error.log'
loglevel = 'info'

# Daemonize the Gunicorn process (run in the background)
# daemon = True
