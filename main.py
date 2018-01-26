#!/usr/bin/env python

import multiprocessing as mp

from stream import Stream
from server import run

import argparse

# Construct the argument parser and parse the arguments.
ap = argparse.ArgumentParser()
ap.add_argument("-p", "--port", type=int, default=80,
	help="port to serve service over")
ap.add_argument("-d", "--debug", type=bool, default=False,
	help="Run service in debug mode.")
ap.add_argument("-pi", "--picamera", type=bool, default=False,
help="Run service in debug mode.")
args = vars(ap.parse_args())

if args["debug"] and args["picamera"]:
    print("Picamera will not work with debugging enabled.")
    exit(0)

if __name__ == '__main__':

    try:
        if args["picamera"]:
            mp.set_start_method('fork')
        else:
            mp.set_start_method('spawn')
    except RuntimeError:
        print("Could not change start method.")

    # Frames are passed in the queue.
    queue = mp.Queue(100)

    stream_process = mp.Process(target=Stream().run, args=(queue,))
    server_process = mp.Process(target=run, args=(queue, args['port']))

    server_process.start()
    stream_process.start()

    stream_process.join()
    server_process.join()