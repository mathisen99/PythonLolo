import logging
from colorama import Fore, Style, init

# initialize colorama
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG:    Fore.CYAN + "%(asctime)s %(name)s %(levelname)s: %(message)s" + Style.RESET_ALL,
        logging.INFO:     Fore.GREEN + "%(asctime)s %(name)s %(levelname)s: %(message)s" + Style.RESET_ALL,
        logging.WARNING:  Fore.YELLOW + "%(asctime)s %(name)s %(levelname)s: %(message)s" + Style.RESET_ALL,
        logging.ERROR:    Fore.RED + "%(asctime)s %(name)s %(levelname)s: %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.MAGENTA + "%(asctime)s %(name)s %(levelname)s: %(message)s" + Style.RESET_ALL,
    }

    def format(self, record):
        # Color WS and IRC message prefixes distinctly
        original = record.getMessage()
        if original.startswith("IRC <<") or original.startswith("IRC >>"):
            record.msg = Fore.YELLOW + original + Style.RESET_ALL
        elif original.startswith("WS <<") or original.startswith("WS >>"):
            record.msg = Fore.MAGENTA + original + Style.RESET_ALL
        else:
            record.msg = original
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    return logger
