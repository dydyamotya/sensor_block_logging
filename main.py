import argparse
import datetime
import pathlib
from tkinter import Tk

from classes import *

if __name__ == "__main__":
    import logging
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", help="Debug state")
    parser.add_argument("-s", "--stdout", action="store_true")
    args = parser.parse_args()
    logs_folder = pathlib.Path().cwd() / "logs"
    logs_folder.mkdir(exist_ok=True)
    logging_file_name = (logs_folder / datetime.datetime.now().strftime("%y%m%d_%H%M%S")).with_suffix(".log")
    logging.basicConfig(filename=None if args.stdout else logging_file_name.as_posix(),
                        filemode='w',
                        level=logging.DEBUG if args.debug else logging.INFO,
                        datefmt="%y%m%d_%H:%M:%S",
                        format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger()

    app = Tk()
    main = MainWindow(master=app)
    main.pack()
    logger.info("Program started")
    logger.debug("In debug mode")
    app.mainloop()
    logger.info("Program stopped")
