# -*- coding: utf-8 -*-
"""
接收 zmq 发来的 log 信息
@author zrong
"""
import zmq
import redis
from pathlib import Path
import time

from pyzog.logging import get_logger


class Receiver(object):
    """ 接收器基类
    """
    # 日志存储文件夹
    logpath = None

    # 所有的日志搜集器
    loggers = None

    # pyzog 自身专用的 logger
    logger = None

    def __init__(self, logpath):
        if isinstance(logpath, str):
            self.logpath = Path(logpath)
        else:
            self.logpath = logpath
        self.logpath.mkdir(parents=True, exist_ok=True)
        self.loggers = {}
        self.logger = get_logger('pyzog', type_='stream', fmt='text')

    def start(self):
        raise ValueError('Implement start!')

    def get_logger(self, name):
        log = self.loggers.get(name)
        if log is None:
            log = get_logger(name, target=self.logpath, type_='file', fmt='raw')
            self.loggers[name] = log
        return log


class ZeroMQReceiver(Receiver):
    """ 接收 ZeroMQ 发来的数据并写入 logpath 文件夹
    """
    # zmq 上下文
    ctx = None

    # zmq socket
    socket = None

    # 监听或者连接的地址
    addr = None

    # ZeroMQ 的模式，默认为订阅模式
    socket_type = zmq.SUB

    def __init__(self, logpath, host, port, socket_type=zmq.SUB):
        super().__init__(logpath)
        self.addr = host + ':' + str(port)
        self.socket_type = socket_type

    def start(self):
        """ 开始接收
        """
        try:
            self.ctx = zmq.Context()
            self.socket = self.ctx.socket(self.socket_type)

            self.socket.bind(self.addr)
            self.logger.warn("ZeroMQ listen addr: %s" % self.addr)
            while True:
                msg = self.socket.recv_string()
                if msg:
                    self.on_receive(msg)
        except Exception as e:
            self.logger.error('Exit:' + repr(e))
            return e

    def on_receive(self, msg):
        logname = 'mjptest'
        log = self.get_logger(logname)
        log.info(msg)


class RedisReceiver(Receiver):
    """ 接收 Redis PUBLISH 发来的数据并写入 logpath 文件夹
    """
    # redis 实例
    r = None

    # pubsub 实例
    pub = None

    # redis 配置
    host = None
    port = None
    password = None
    db = 0
    channel = None

    def __init__(self, logpath, host='localhost', port=6379, password=None, db=0, channel=['pyzog.*']):
        super().__init__(logpath)
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.channel = channel

    def start(self):
        """ 开始接收
        """
        try:
            self.r = redis.Redis(host=self.host, port=self.port, password=self.password, db=self.db)
            self.pub = self.r.pubsub(ignore_subscribe_messages=True)
            self.pub.psubscribe(*self.channel)

            self.logger.warn("Redis connect addr: %s@%s:%s/%s" % (self.host, self.port, self.password or '', self.db))

            while True:
                msg = self.pub.get_message()
                if msg:
                    self.on_receive(msg)
                time.sleep(0.001)
                if not msg:
                    self.pub.check_health()
                    ping = self.pub.ping('PING ' + str(time.time()))
                    self.logger.warn('PING: %s', ping)
        except Exception as e:
            self.pub.close()
            self.logger.error('Exit:' + repr(e))
            return e

    def on_receive(self, msg):
        channel = msg.get('channel')
        data = msg.get('data')
        if isinstance(channel, bytearray) and  isinstance(data, bytearray):
            logname = channel.decode()
            log = self.get_logger(logname)
            log.info(data.decode())
        else:
            self.logger.error('channel: %s, data: %s, type: %s', channel, data, msg.get('type'))
