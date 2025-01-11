import logging  
import os  
  
def configure_logger():  
    logger = logging.getLogger()  
    logger.setLevel(logging.INFO)  

    cur_dir = os.path.dirname(os.path.abspath(__file__))
    par_dir = os.path.dirname(cur_dir)
    log_dir = os.path.join(par_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)  

    print(f"Log dir: {log_dir}")
    print(f"Log dir created: {os.path.exists(log_dir)}")

    file_handler = logging.FileHandler(os.path.join(log_dir, 'app.log'))  
    file_handler.setLevel(logging.INFO)  
  
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')  
    file_handler.setFormatter(formatter)  
  
    logger.addHandler(file_handler)  
  
    console_handler = logging.StreamHandler()  
    console_handler.setLevel(logging.INFO)  
    console_handler.setFormatter(formatter)  
    logger.addHandler(console_handler)  
  
def get_logger(name):  
    return logging.getLogger(name)  

