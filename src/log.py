from datetime import datetime
from time import time

def _print(*args):
    time = datetime.now().time().isoformat()[:8]
    print time,
    print " ".join(map(str, args))
