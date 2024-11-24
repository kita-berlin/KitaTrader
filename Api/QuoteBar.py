import os
import struct
from datetime import datetime, timedelta
from xmlrpc.client import boolean


######################################
class QuoteBar:
    Time: datetime = datetime.min
    milli_seconds: int = 0
    Open: float = 0
    High: float = 0
    Low: float = 0
    Close: float = 0
    Volume: int = 0
    open_ask: float = 0
