import traceback
from datetime import datetime
from functools import wraps

def error_handle(func):
    @wraps(func)
    def wrapper_error_handle(*args):
        try:
            return func(*args)
        except:
            tb = traceback.format_exc()
            with open("RevisedBots/error_logs.txt", "a") as log:
                log.write(f"{datetime.now().date().strftime('%m_%d_%Y')} | {func.__name__.replace("start_", "")} - {str(tb)}\n")
    return wrapper_error_handle