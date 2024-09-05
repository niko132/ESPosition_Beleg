from util import *
import numpy as np
import threading
import time
from queue import Queue
import pandas as pd

def get_test_anchors():
    anchor_positions_in_px = {
        "000000000001": (30, 560),
        "000000000002": (550, 600),
        "000000000003": (60, 30),
    }
    
    anchor_positions_in_m = { mac: (env_to_m(x_px), env_to_m(y_px)) for (mac, (x_px, y_px)) in anchor_positions_in_px.items() }
    
    return anchor_positions_in_m

class ESPositionMainNodeSimulator:

    def __init__(self, anchors, target_mac, target_position, round_rssi=False, randomize=False, message_every_ms=100, auto_move=False):
        self.anchors = anchors
        self.target_mac = target_mac
        self.target_position = target_position
        self.round_rssi = round_rssi
        self.randomize = randomize
        self.message_queue = Queue(maxsize = 0)
        
        self.current_anchor_idx = 0
        
        message_thread = threading.Thread(target=self.generate_messages_func, args=(message_every_ms,), daemon=True)
        message_thread.start()
        
        if auto_move:
            move_thread = threading.Thread(target=self.auto_move_func, daemon=True)
            move_thread.start()
    
    def readline(self):
        return self.message_queue.get()
    
    def set_target_pos(self, target_position):
        self.target_position = target_position
        
    def get_target_pos(self):
        return self.target_position
    
    def generate_messages_func(self, every_ms):
        while True:
            anchor_mac = list(self.anchors.keys())[self.current_anchor_idx]
            anchor_position = list(self.anchors.values())[self.current_anchor_idx]
            
            distance = dist(self.target_position, anchor_position)
            rssi = path_loss_model(distance)
            
            if self.randomize:
                noise = np.random.normal(0, 1, 1)[0]
                rssi = rssi + noise
            
            if self.round_rssi:
                rssi = round(rssi)
            
            self.current_anchor_idx = (self.current_anchor_idx + 1) % len(self.anchors)
            
            message = f"{anchor_mac}_{self.target_mac}:{rssi}".encode("utf-8")
            
            self.message_queue.put(message)
            
            time.sleep(every_ms / 1000.0)
    
    def auto_move_func(self):
        while True:
            time.sleep(0.2)
            self.move(0.1)
    
    def move(self, move_by=1.0):
        x = self.target_position[0] + move_by
        y = self.target_position[1]
        
        if x > 7:
            x = move_by
            y = y + move_by
            
        if y > 7:
            y = 1
        
        self.target_position = (x, y)

class ESPositionMainNodePlayback:

    def __init__(self, target_mac, filepath):
        self.target_mac = target_mac
        self.filepath = filepath
        self.message_queue = Queue(maxsize = 0)
        
        message_thread = threading.Thread(target=self.generate_messages_func, args=(filepath,), daemon=True)
        message_thread.start()
    
    def readline(self):
        return self.message_queue.get()
    
    def generate_messages_func(self, filepath):
        df = pd.read_csv(filepath, index_col=False)
        df_sorted = df.sort_values(by=['timestamp'], ascending=True)
        from_timestamp = float(df_sorted['timestamp'].iloc[0])
        last_time = time.time()
    
        while True:
            current_time = time.time()
            diff_time = current_time - last_time
            
            to_timestamp = from_timestamp + diff_time
            
            new_rows = df_sorted.loc[(df_sorted['timestamp'] >= from_timestamp) & (df_sorted['timestamp'] < to_timestamp)]
            for index, row in new_rows.iterrows():
                message = f"{row['monitor_mac']}_{row['target_mac']}:{row['rssi']}".encode("utf-8")
                self.message_queue.put(message)
            
            
            from_timestamp = to_timestamp
            last_time = current_time
            
            time.sleep(100.0 / 1000.0)
    
    def get_anchors(self):
        df = pd.read_csv(self.filepath, index_col=False)
        df_unique_monitors = df.drop_duplicates('monitor_mac')
        
        anchor_positions = {}
        
        for index, row in df_unique_monitors.iterrows():
            message = f"{row['monitor_mac']}_{row['target_mac']}:{row['rssi']}".encode("utf-8")
            anchor_positions[row['monitor_mac']] = (float(row['anchor_position_x']), float(row['anchor_position_y']))
        
        return anchor_positions