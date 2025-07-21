import logging
import sys
from typing import Optional


def setup_logging(
    level: int = logging.INFO, format_string: Optional[str] = None
) -> None:
    """Configure application logging."""
    if format_string is None:
        format_string = '%(asctime)s [%(levelname)-8s] [%(name)s] %(message)s'

    logging.basicConfig(
        level=level, format=format_string, handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger('httpcore').setLevel(logging.INFO)
    logging.getLogger('httpx').setLevel(logging.WARNING)
