# -*- coding: utf-8 -*-
"""
接收 zmq 发来的 log 信息
@author zrong
"""
import zmq
import redis
from pathlib import Path
from . import get_logger, logger


class Receiver(object):
    """ 接收器基类
    """
    # 日志存储文件夹
    logpath = None

    # 监听或者连接的地址
    addr = None

    # 所有的日志搜集器
    loggers = None

    def __init__(self, addr, logpath):
        self.addr = addr
        if isinstance(logpath, str):
            self.logpath = Path(logpath)
        else:
            self.logpath = logpath
        self.logpath.mkdir(parents=True, exist_ok=True)
        self.loggers = {}

    def start(self):
        raise ValueError('Implement start!')

    def get_logger(self, name):
        log = self.loggers.get(name)
        if log is None:
            log = get_logger(name, self.logpath, type_='file', fmt='raw')
            self.loggers[name] = log
        return log


class ZeroMQReceiver(Receiver):
    """ 接收 ZeroMQ 发来的数据并写入 logpath 文件夹
    """
    # zmq 上下文
    ctx = None

    # zmq socket
    socket = None

    def start(self):
        """ 开始接收
        """
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PULL)

        self.socket.bind(self.addr)
        logger.warn("ZeroMQ listen addr: %s" % self.addr)

        try:
            while True:
                msg = self.socket.recv_string()
                self.on_receive(msg)
        except (KeyboardInterrupt, SystemExit) as e:
            logger.error('Exit:' + repr(e))

    def on_receive(self, msg):
        logname = 'mjptest'
        log = self.get_logger(logname)
        log.info(msg)


class RedisReceiver(object):
    """ 接收 Redis PUBLISH 发来的数据并写入 logpath 文件夹
    """
    # redis 实例
    r = None

    # pubsub 实例
    pub = None

    def start(self):
        """ 开始接收
        """
        address = self.addr.split(':')
        self.r = redis.Redis(host=address[0], port=int(address[1]), db=0)
        self.pub = self.r.pubsub()

        logger.warn("Redis connect addr: %s" % self.addr)

        try:
            while True:
                msg = self.pub.get_message()
                self.on_receive(msg)
        except (KeyboardInterrupt, SystemExit) as e:
            self.pub.close()
            logger.error('Exit:' + repr(e))

    def on_receive(self, msg):
        logname = 'mjptest'
        log = self.get_logger(logname)
        log.info(msg)
