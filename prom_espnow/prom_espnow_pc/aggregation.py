from abc import ABC, abstractmethod
import numpy as np
from collections import deque
import time

DEFAULT_LEN_RSSI_QUEUE = 10  # store at most 10 RSSI values per target and per monitor

class PacketItem:
    identification: int
    timestamp: float
    rssi: float
    
    def __init__(
            self,
            identification: int,
            timestamp: float,
            rssi: int
        ) -> None:
        self.identification = identification
        self.timestamp = timestamp
        self.rssi = rssi
        
    def __repr__(self):
        return f'PacketItem({self.identification}: {self.timestamp}, {self.rssi})'

class PacketAggregation(ABC):

    @abstractmethod
    def add_packet(self, packetItem):
        pass
    
    @abstractmethod
    def get_packet(self):
        pass
        
class MostRecentPacketAggregation(PacketAggregation):

    def add_packet(self, packetItem):
        self.item = packetItem
    
    def get_packet(self):
        return self.item

class MeanPacketAggregation(PacketAggregation):

    def __init__(self, window_size=DEFAULT_LEN_RSSI_QUEUE):
        self.queue = deque([], maxlen=window_size)

    def add_packet(self, packetItem):
        self.queue.appendleft(packetItem)
    
    def get_packet(self):
        items = list(self.queue)
        mean_rssi = np.mean([item.rssi for item in items])
        timestamp = time.time()
        return PacketItem(0, timestamp, mean_rssi)

class MedianPacketAggregation(PacketAggregation):

    def __init__(self, window_size=DEFAULT_LEN_RSSI_QUEUE):
        self.queue = deque([], maxlen=window_size)

    def add_packet(self, packetItem):
        self.queue.appendleft(packetItem)
    
    def get_packet(self):
        items = list(self.queue)
        mean_rssi = np.median([item.rssi for item in items])
        timestamp = time.time()
        return PacketItem(0, timestamp, mean_rssi)

class KalmanFilter:
    def __init__(self, process_variance, measurement_variance, estimated_measurement):
        self.process_variance = process_variance
        self.measurement_variance = measurement_variance
        self.estimated_measurement = estimated_measurement
        self.error_estimate = 1.0
    
    def update(self, measurement):
        kalman_gain = self.error_estimate / (self.error_estimate + self.measurement_variance)
        self.estimated_measurement += kalman_gain * (measurement - self.estimated_measurement)
        self.error_estimate = (1.0 - kalman_gain) * self.error_estimate + abs(self.estimated_measurement) * self.process_variance
        return self.estimated_measurement

class KalmanFilterPacketAggregation(PacketAggregation):

    def __init__(self):
        self.kalman_filter = KalmanFilter(process_variance=1e-3, measurement_variance=10.0, estimated_measurement=-50.0)

    def add_packet(self, packetItem):
        self.filtered_rssi = self.kalman_filter.update(packetItem.rssi)  # Smooth the adjusted RSSI value
    
    def get_packet(self):
        timestamp = time.time()
        return PacketItem(0, timestamp, self.filtered_rssi)