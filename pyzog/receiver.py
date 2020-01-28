# -*- coding: utf-8 -*-
"""
接收 zmq 发来的 log 信息
@author zrong
"""
import zmq
from pathlib import Path
from . import get_logger, logger

class Receiver(object):
    """ 接收 ZeroMQ 发来的数据并写入 logpath 文件夹
    """
    # zmq 上下文
    ctx = None

    # zmq socket
    socket = None

    # 所有的日志搜集器
    loggers = None

    # 接收日志的端口
    port = 0

    # 日志存储文件夹
    logpath = None

    def __init__(self, port, logpath):
        self.port = port
        self.logpath = logpath
        if isinstance(logpath, str):
            self.logpath = Path(logpath)
        else:
            self.logpath = logpath
        self.logpath.mkdir(parents=True, exist_ok=True)
        self.loggers = {}

    def start(self):
        """
        开始接收
        :param port: 接收日志的端口
        :param logpath: 存日志的目录
        :return:
        """
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PULL)

        addr = "tcp://*:%d" % self.port
        self.socket.bind(addr)
        logger.warn("ZeroMQ listen addr: %s" % addr)

        try:
            while True:
                msg = self.socket.recv_string()
                self.on_receive(msg)
        except (KeyboardInterrupt, SystemExit) as e:
            logger.error('exit:' + repr(e))

    def on_receive(self, msg):
        logname = 'mjptest'
        log = self.get_logger(logname)
        log.info(content)

    def get_logger(self, name):
        log = self.loggers.get(name)
        if log is None:
            log = get_logger(name, self.logpath, type_='file', fmt='raw')
            self.loggers[name] = log
        return log
