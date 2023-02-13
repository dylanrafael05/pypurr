import os
import time
import threading


_last_ping_t: float = 0
_ping_timeout: float = 0


def set_ping_timeout(f: float):
    global _ping_timeout
    _ping_timeout = f


def ping():
    global _last_ping_t
    _last_ping_t = time.time()


def begin_ping_checking():

    def ping_checker():
        while True:
            if time.time() - _last_ping_t > _ping_timeout:

                print()
                print(f','+'-'*70)
                print(f'|  Application has been busy for {_ping_timeout} sec. Killing process . . .')
                print(f'`'+'-'*70)

                # noinspection PyUnresolvedReferences, PyProtectedMember
                os._exit(-1)

    ping()

    p_thr = threading.Thread(target=ping_checker, name='<Ping Checker>')
    p_thr.daemon = True
    p_thr.start()