import sys
from os import get_terminal_size
from enum import Enum
from tqdm import tqdm

from zotify.config import *
from zotify.zotify import Zotify


class PrintChannel(Enum):
    SPLASH = PRINT_SPLASH
    SKIPS = PRINT_SKIPS
    ERRORS = PRINT_ERRORS
    WARNINGS = PRINT_WARNINGS
    DOWNLOADS = PRINT_DOWNLOADS
    API_ERRORS = PRINT_API_ERRORS
    PROGRESS_INFO = PRINT_PROGRESS_INFO


ERROR_CHANNEL = [PrintChannel.ERRORS, PrintChannel.API_ERRORS]


class Printer:
    @staticmethod
    def print(channel: PrintChannel, msg: str) -> None:
        if Zotify.CONFIG.get(channel.value):
            columns, _ = get_terminal_size()
            file = sys.stdout
            if channel in ERROR_CHANNEL:
                file = sys.stderr
            for line in msg.splitlines():
                numblines = 1 + (len(line) // columns)
                print(' ' * columns * numblines 
                      + "\033[A" * (numblines - 1) 
                      + "\r" + line, file=file)

    @staticmethod
    def print_loader(channel: PrintChannel, msg: str) -> None:
        if Zotify.CONFIG.get(channel.value):
            columns, _ = get_terminal_size()
            print("\r\033[A" 
                  + ' ' * columns 
                  + '\r' + msg, flush=True)

    @staticmethod
    def progress(iterable=None, desc=None, total=None, unit='it', disable=False, unit_scale=False, unit_divisor=1000, pos=1):
        return tqdm(iterable=iterable, desc=desc, total=total, disable=disable, unit=unit, unit_scale=unit_scale, unit_divisor=unit_divisor, position=pos, leave=False)