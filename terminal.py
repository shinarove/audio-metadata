from enum import Enum

import common as cm

class TerminalResult(Enum):
    EXIT = -1
    FAILED = 0
    SUCCESS = 1

def ask_input_str(prompt: str, default: str=None) -> tuple[TerminalResult, str | None]:
    """
    Ask user input for string value with optional default value.

    Args:
        prompt (str): The prompt to be displayed.
        default (str, optional): The default value to be displayed.
    Returns:
        tuple[TerminalResult, str | None]: A tuple with the terminal result and the input value.
        If an inconsistent state or a keyboard interrupt occurs, the return value is None.
    """
    try:
        val = input(f"{prompt} [{'default: ' + default if default else ''}]: ").strip()
    except KeyboardInterrupt:
        cm.log(cm.LogLevel.INFO, f"Keyboard interrupt, exiting.")
        return TerminalResult.EXIT, None
    if not val and not default:
        cm.log(cm.LogLevel.ERROR, f"No value and no default provided!")
        return TerminalResult.FAILED, None

    if not val and default:
        return TerminalResult.SUCCESS, default
    return TerminalResult.SUCCESS, val

def ask_input_int(prompt: str, default: int=None) -> tuple[TerminalResult, int]:
    """
    Ask user input for integer value with optional default value.

    Args:
        prompt (str): The prompt to be displayed.
        default (int, optional): The default value to be displayed. Default is None.
    Returns:
        tuple[TerminalResult, int]: A tuple with the terminal result and the input value.
    """
    try:
        val = input(f"{prompt} [{'default: ' + str(default) if default else ''}]: ").strip()
    except KeyboardInterrupt:
        cm.log(cm.LogLevel.INFO, f"Keyboard interrupt, exiting.")
        return TerminalResult.EXIT, default

    try:
        int_val = int(val)
    except (ValueError, TypeError):
        cm.log(cm.LogLevel.ERROR, f"Invalid integer provided!")
        return TerminalResult.FAILED, default

    return TerminalResult.SUCCESS, int_val

def ask_input_bool(prompt: str, default: bool=False) -> tuple[TerminalResult, bool]:
    """
    Ask user input for boolean value (y/n) with default value.

    Args:
        prompt (str): The prompt to be displayed.
        default (bool): The default value to be displayed. Default is False.
    Returns:
        tuple[TerminalResult, bool]: A tuple with the terminal result and the boolean value.
    """
    try:
        val = input(f"{prompt} [y/n]: ").strip().lower()
    except KeyboardInterrupt:
        cm.log(cm.LogLevel.INFO, f"Keyboard interrupt, exiting.")
        return TerminalResult.EXIT, default

    if val == "":
        return TerminalResult.SUCCESS, default
    elif val in ("y", "yes"):
        return TerminalResult.SUCCESS, True
    elif val in ("n", "no"):
        return TerminalResult.SUCCESS, False
    else:
        cm.log(cm.LogLevel.ERROR, f"Invalid boolean value provided!")
        return TerminalResult.FAILED, default