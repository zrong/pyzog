# -*- coding: utf-8 -*-
"""
接收 zmq 发来的 log 信息
@author zrong
"""
import zmq
import redis
from pathlib import Path
import time
import socket

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
    channels = None

    # 保活，每隔一定时间 ping 一次
    ping_ts = 0
    ping_interval = 60
    thread = None
    sleep_time = 0.0005
    get_message_type = 'thread'

    # tcp_keep = {socket.TCP_KEEPIDLE: 120, socket.TCP_KEEPCNT: 2, socket.TCP_KEEPINTVL: 30}
    tcp_keep = None

    def __init__(self, logpath, host='localhost', port=6379, password=None, db=0, channels=['pyzog.*'], get_message_type='thread', sleep_time=0.0005):
        super().__init__(logpath)
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.channels = channels
        self.get_message_type = get_message_type
        self.sleep_time = sleep_time

    def start(self):
        """ 开始接收
        """
        try:
            self.init_redis()
            fun = getattr(self, 'sub_' + self.get_message_type)
            self.logger.warn('RedisReceiver use %s to get_message, channels is %s, sleep_time is %s', self.get_message_type, self.channels, self.sleep_time)
            fun()
        except Exception as e:
            self.pub.close()
            self.logger.error('RedisReceiver.Exit:' + repr(e))
            return e

    def init_redis(self):
        self.r = redis.Redis(host=self.host, port=self.port, password=self.password, db=self.db,
            health_check_interval=self.ping_interval,
            socket_keepalive=True,
            socket_keepalive_options=self.tcp_keep)
        self.pub = self.r.pubsub(ignore_subscribe_messages=True)
        self.logger.warn("RedisReceiver.init_redis %s:%s:%s/%s" % (self.password or '', self.host, self.port, self.db))

    def sub_block(self):
        self.pub.psubscribe(*self.channels)
        while True:
            msg = self.pub.get_message()
            self.check_message(msg)
            time.sleep(self.sleep_time)

    def sub_listen(self):
        self.pub.psubscribe(*self.channels)
        for message in self.pub.listen():
            self.check_message(message)

    def sub_thread(self):
        def message_handler(msg):
            self.check_message(msg)
        handles = {}
        for ch in self.channels:
            handles[ch] = message_handler
        self.pub.psubscribe(**handles)
        self.thread = self.pub.run_in_thread(sleep_time=self.sleep_time, daemon=True)
        self.thread.join()

    def check_message(self, msg):
        try:
            if msg:
                self.on_receive(msg)
            ts = time.time()
            if ts - self.ping_ts > self.ping_interval:
                self.ping_ts = ts
                self.pub.check_health()
                self.logger.warn('RedisReceiver.get_message check_health: %s', ts)
        except AttributeError as e:
            self.logger.error('RedisReceiver.get_message AttributeError:' + repr(e))

    def on_receive(self, msg):
        channel = msg.get('channel')
        data = msg.get('data')
        if isinstance(channel, bytes) and isinstance(data, bytes):
            logname = channel.decode()
            log = self.get_logger(logname)
            log.info(data.decode())
        else:
            self.logger.error('RedisReceiver.on_receive channel: %s, data: %s, type: %s', channel, data, msg.get('type'))
