# gunicorn.conf.py  
import os  
  
# Determine the project root directory  
project_root = os.path.dirname(os.path.abspath(__file__))  
  
# Socket to bind  
bind = f'unix:{project_root}/gunicorn.sock'  
  
# Configurations based on Google Cloud documentation  
workers = 2 
forwarded_allow_ips = '*'  
secure_scheme_headers = {'X-FORWARDED-PROTO': 'https'}  
  
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))  
  
# The maximum number of requests a worker will process before restarting  
max_requests = 1000  
  
# Logging configuration  
log_dir = os.path.join(project_root, 'logs')  
os.makedirs(log_dir, exist_ok=True)  # Ensure the log directory exists  
  
accesslog = os.path.join(log_dir, 'gunicorn-access.log')  
errorlog = os.path.join(log_dir, 'gunicorn-error.log')  
loglevel = 'info'  
  
# Daemonize the Gunicorn process (run in the background)  
daemon = False  # Set to False to allow systemd to manage the process  
