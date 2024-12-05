#include <WiFi.h>
#include <esp_wifi.h>  // ESP32 specific low-level WiFi functions

#define QUEUE_SIZE 1000  // Queue size for packet data
const int WIFI_CHANNEL = 1;
const uint8_t targetMAC[6] = { 0xDA, 0x9E, 0xC7, 0xF5, 0x5B, 0xEB };  // Replace with your target MAC address

// Structure to hold packet data
struct PacketData {
  uint32_t timestamp;
  int8_t rssi;
};

// Define a queue to store packet data
QueueHandle_t packetQueue;

// Promiscuous mode callback
void IRAM_ATTR promiscuousCallback(void* buf, wifi_promiscuous_pkt_type_t type) {
  wifi_promiscuous_pkt_t *pkt = (wifi_promiscuous_pkt_t*) buf;

  // Check if packet length is sufficient to contain a MAC address
  if (pkt->rx_ctrl.sig_len < 12)
    return;

  uint8_t *srcMAC = pkt->payload + 10;  // Source MAC address is at offset 10 in payload

  // Use memcmp to compare MAC addresses; return immediately if no match
  if (memcmp(srcMAC, targetMAC, 6) != 0)
    return;

  // Prepare packet data if MAC matches
  PacketData packet;
  packet.timestamp = micros();  // Capture timestamp
  packet.rssi = pkt->rx_ctrl.rssi;  // Capture RSSI

  // Send packet data to the queue (non-blocking)
  xQueueSendFromISR(packetQueue, &packet, NULL);
}

void setup() {
  Serial.begin(115200);

  // Initialize the WiFi in station mode
  WiFi.mode(WIFI_MODE_STA);
  WiFi.disconnect();  // Ensure we are not connected to any network

  // Create a queue to hold packet data
  packetQueue = xQueueCreate(QUEUE_SIZE, sizeof(PacketData));
  if (packetQueue == NULL) {
    Serial.println("Failed to create packet queue");
    while (1);
  }

  // Enable promiscuous mode
  esp_wifi_set_promiscuous(true);
  esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);
  esp_wifi_set_promiscuous_rx_cb(promiscuousCallback);
}

void loop() {
  PacketData packet;

  // Check if there's data available in the queue
  if (xQueueReceive(packetQueue, &packet, portMAX_DELAY)) {
    // Process the packet data (e.g., send over serial)
    Serial.print(packet.timestamp);
    Serial.print(":");
    Serial.println(packet.rssi);
  }
}