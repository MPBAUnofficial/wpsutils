from time import sleep
from .wpsutils_settings import POLLING_TIMEOUT

try:
    from multiprocessing import Process
except ImportError:
    from threading import Thread as Process

class RefreshProcess(Process):
    def __init__(self, refresh_model):
        super(RefreshProcess,self).__init__()
        self._refresh_model = refresh_model

    def run(self):
        while True:
            to_be_refreshed = self._refresh_model.objects.to_update()
            for proc in to_be_refreshed:
                proc.poll_and_update()

            sleep(POLLING_TIMEOUT)

