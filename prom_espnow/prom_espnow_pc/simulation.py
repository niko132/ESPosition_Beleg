from util import *

def get_test_anchors():
    anchor_positions_in_px = {
        "000000000001": (30, 560),
        "000000000002": (550, 600),
        "000000000003": (60, 30),
    }
    
    anchor_positions_in_m = { mac: (env_to_m(x_px), env_to_m(y_px)) for (mac, (x_px, y_px)) in anchor_positions_in_px.items() }
    
    return anchor_positions_in_m

class ESPositionMainNodeSimulator:

    def __init__(self, anchors, target_mac, target_position, round_rssi=False):
        self.anchors = anchors
        self.target_mac = target_mac
        self.target_position = target_position
        self.round_rssi = round_rssi
        
        self.current_anchor_idx = 0
    
    def readline(self):
        anchor_mac = list(self.anchors.keys())[self.current_anchor_idx]
        anchor_position = list(self.anchors.values())[self.current_anchor_idx]
        
        distance = dist(self.target_position, anchor_position)
        rssi = path_loss_model(distance)
        
        if self.round_rssi:
            rssi = round(rssi)
        
        self.current_anchor_idx = (self.current_anchor_idx + 1) % len(self.anchors)
        
        return f"{anchor_mac}_{self.target_mac}:{rssi}".encode("utf-8")
    
    def set_target_pos(self, target_position):
        self.target_position = target_position
        
    def get_target_pos(self):
        return self.target_position
    
    def move(self):
        x = self.target_position[0] + 1
        y = self.target_position[1]
        
        if x > 7:
            x = 1
            y = y + 1
            
        if y > 7:
            y = 1
        
        self.target_position = (x, y)