from pathlib import Path

import pyzog
from pyzog.receiver import Receiver
import pytest

port = 5011

@pytest.fixture(scope='session')
def receiver():
    r = Receiver(5011, pyzog.here.joinpath('logs'))
    yield r
