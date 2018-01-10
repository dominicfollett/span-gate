#!/usr/bin/env python

import multiprocessing as multiprocessing
from stream import Stream
from server import Server


if __name__ == '__main__':
    # 'fork' by default.
    mp.set_start_method('fork')
    
    # Frames are passed in the queue.
    queue = mp.Queue()

    # How is the queue shared between processes?
    stream_process = mp.Process(target=Stream().run, args=(queue,))
    server_process = mp.Process(target=Server().run, args=(queue,))

    stream_process.start()
    server_process.start()

    stream_process.join()
    server_process.join()