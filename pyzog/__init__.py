# -*- coding: utf-8 -*-
__version__ = '0.1.1'


from pathlib import Path
import logging 
from logging.handlers import WatchedFileHandler

import zmq
import redis
from pythonjsonlogger import jsonlogger


TEXT_LOG_FORMAT = """
[%(asctime)s] %(levelname)s in %(module)s.%(funcName)s [%(pathname)s:%(lineno)d]:
%(message)s"""
JSON_LOG_FORMAT = r'%(levelname)s %(module)s %(funcName)s %(pathname)s %(lineno) %(threadName) %(processName) %(message)'


class PUSHHandler(logging.Handler):
    """A basic logging handler that emits log messages through a PUSH socket.

    Takes a PUSH socket already bound to interfaces or an interface to bind to.

    Example::

        sock = context.socket(zmq.PUSH)
        sock.connect('tcp://192.168.0.1:5050')
        handler = PUSHHandler(sock)

    Or::

        handler = PUBHandler('tcp://192.168.1:5050')

    These are equivalent.
    """
    socket = None
    ctx = None
    
    def __init__(self, interface_or_socket, context=None):
        logging.Handler.__init__(self)
        if isinstance(interface_or_socket, zmq.Socket):
            self.socket = interface_or_socket
            self.ctx = self.socket.context
        else:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.PUSH)
            self.socket.connect(interface_or_socket)

    def emit(self, record):
        """Emit a log message on my socket."""
        msg = self.format(record)
        try:
            self.socket.send_string(msg)
        except TypeError:
            raise
        except (ValueError, zmq.ZMQError):
            self.handleError(record)


class SUBSCRIBEHandler(logging.Handler):
    """A basic logging handler that emits log messages through a PUSH socket.

    Takes a PUSH socket already bound to interfaces or an interface to bind to.

    Example::

        sock = context.socket(zmq.PUSH)
        sock.connect('tcp://192.168.0.1:5050')
        handler = PUSHHandler(sock)

    Or::

        handler = PUBHandler('tcp://192.168.1:5050')

    These are equivalent.
    """
    socket = None
    ctx = None
    
    def __init__(self, interface_or_socket, context=None):
        logging.Handler.__init__(self)
        if isinstance(interface_or_socket, zmq.Socket):
            self.socket = interface_or_socket
            self.ctx = self.socket.context
        else:
            self.ctx = context or zmq.Context()
            self.socket = self.ctx.socket(zmq.PUSH)
            self.socket.connect(interface_or_socket)

    def emit(self, record):
        """Emit a log message on my socket."""
        msg = self.format(record)
        try:
            self.socket.send_string(msg)
        except TypeError:
            raise
        except (ValueError, zmq.ZMQError):
            self.handleError(record)


def _create_file_handler(target, filename):
    """ 创建一个基于文件的 logging handler
    :param target: 一个 Path 对象，或者一个 path 字符串
    """
    logsdir = target if isinstance(target, Path) else Path(target)
    # 创建或者设置 logs 文件夹的权限，让其他 user 也可以写入（例如nginx）
    # 注意，要设置 777 权限，需要使用 0o40777 或者先设置 os.umask(0)
    # 0o40777 是根据 os.stat() 获取到的 st_mode 得到的
    if logsdir.exists():
        logsdir.chmod(0o40777)
    else:
        logsdir.mkdir(mode=0o40777)
    logfile = logsdir.joinpath(filename + '.log')
    if not logfile.exists():
        logfile.touch()
    # 使用 WatchedFileHandler 在文件改变的时候自动打开新的流，配合 logrotate 使用
    return WatchedFileHandler(logfile, encoding='utf8')


def _create_zmq_handler(target):
    """ 创建一个基于 zeromq 的 logging handler
    :param target: 一个字符串，形如： tcp://127.0.0.1:8334
    """
    return PUSHHandler(target)


def get_logging_handler(type_, fmt, level, target=None, name=None) :
    """ 获取一个 logger handler

    :param type_: stream/file/zmq
    :param fmt: raw/text/json raw 代表原样写入，不增加内容
    :param level: logging 的 level 级别
    :param target: 项目主目录的的 path 字符串或者 Path 对象，也可以是 tcp://127.0.0.1:8334 这样的地址
    :param name: logger 的名称，不要带扩展名
    """
    handler = None
    if type_ == 'zmq':
        if target is None:
            raise TypeError('target is necessary if type is zmq!')
        handler = _create_zmq_handler(target)
    elif type_ == 'file':
        if target is None or name is None:
            raise TypeError('target and name is necessary if type is file!')
        handler = _create_file_handler(target, name)
    else:
        handler = logging.StreamHandler()
    if fmt == 'raw':
        formatter = logging.Formatter()
    elif fmt == 'text':
        formatter = logging.Formatter(TEXT_LOG_FORMAT)
    else:
        formatter = jsonlogger.JsonFormatter(JSON_LOG_FORMAT, timestamp=True)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    return handler


def get_logger(name, target, type_='file', fmt='text', level=logging.INFO):
    """ 基于 target 创建一个 logger

    :param name: logger 的名称，不要带扩展名
    :param target: 项目主目录的的 path 字符串或者 Path 对象，也可以是 tcp://127.0.0.1:8334 这样的地址
    :param type_: stream/file/zmq
    :param fmt: raw/text/json
    :param level: logging 的 level 级别
    """
    hdr = get_logging_handler(type_, fmt, level, target, name)

    log = logging.getLogger(name)
    log.addHandler(hdr)
    log.setLevel(level)
    return log


here = Path(__file__).parent.parent
logger = get_logger('pyzog', here.joinpath('logs'), type_='file', fmt='json')