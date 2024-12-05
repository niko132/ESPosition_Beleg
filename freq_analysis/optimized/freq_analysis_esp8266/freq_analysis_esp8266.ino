#include <ESP8266WiFi.h>

#define BUFFER_SIZE 1000  // Define buffer size for packet data
const int WIFI_CHANNEL = 1;
const uint8_t targetMAC[6] = { 0xDA, 0x9E, 0xC7, 0xF5, 0x5B, 0xEB };  // Replace with your target MAC address

// Structure definition for the sniffer buffer (specific to ESP8266)
struct RxControl {
  signed rssi:8;          // signal intensity of packet
  unsigned rate:4;
  unsigned is_group:1;
  unsigned reserved:1;
  unsigned sig_mode:2;    // 0: 11n packet; 1: non-11n packet;
  unsigned legacy_length:12; // if not 11n packet, shows length of packet.
  unsigned damatch0:1;
  unsigned damatch1:1;
  unsigned bssidmatch0:1;
  unsigned bssidmatch1:1;
  unsigned MCS:7;         // if is 11n packet, shows the modulation and code scheme.
  unsigned CWB:1;         // if is 11n packet, shows if is HT40 packet or not.
  unsigned HT_length:16;  // if is 11n packet, shows length of packet.
  unsigned Smoothing:1;
  unsigned Not_Sounding:1;
  unsigned Aggregation:1;
  unsigned STBC:2;
  unsigned FEC_CODING:1;  // if is 11n packet, shows if is LDPC packet or not.
  unsigned SGI:1;
  unsigned rxend_state:8;
  unsigned ampdu_cnt:8;
  unsigned channel:4;     // which channel this packet in.
  unsigned reserved2:12;
};

struct sniffer_buf {
  struct RxControl rx_ctrl;
  uint8_t buf[112];  // 2nd byte of MAC header
  uint16_t cnt;      // number count of packet
  uint16_t len;      // length of packet
};

// Structure to hold packet data (e.g., timestamp and RSSI)
struct PacketData {
  uint32_t timestamp;
  int8_t rssi;
};

// Circular buffer to store packet data
volatile PacketData packetBuffer[BUFFER_SIZE];
volatile int writeIndex = 0;  // Index for writing new data
volatile int readIndex = 0;   // Index for reading data
volatile bool bufferFull = false;

// Promiscuous mode callback
void ICACHE_RAM_ATTR promiscuousCallback(uint8_t *buf, uint16_t len) {
  struct sniffer_buf *sniffer = (struct sniffer_buf*) buf;

  // Check if packet length is sufficient to contain a MAC address
  if (len < 12)
    return;

  uint8_t *srcMAC = sniffer->buf + 10;  // Source MAC address is at offset 10

  // Use memcmp to compare MAC addresses; return immediately if no match
  if (memcmp(srcMAC, targetMAC, 6) != 0)
    return;

  // Only store data if MAC matches
  if (!bufferFull) {
    PacketData packet;
    packet.timestamp = micros();  // Capture timestamp
    packet.rssi = sniffer->rx_ctrl.rssi;  // Capture RSSI

    // Store the packet data in the buffer using memcpy to avoid copy-constructor issues
    memcpy((void*)&packetBuffer[writeIndex], &packet, sizeof(PacketData));
    writeIndex = (writeIndex + 1) % BUFFER_SIZE;

    // Check if buffer is full
    if (writeIndex == readIndex) {
      bufferFull = true;
    }
  }
}

void setup() {
  Serial.begin(115200);
  WiFi.mode(WIFI_OFF);
  WiFi.setOutputPower(0);

  // Enable promiscuous mode
  wifi_set_opmode(STATION_MODE);
  wifi_set_channel(WIFI_CHANNEL);
  wifi_promiscuous_enable(1);
  wifi_set_promiscuous_rx_cb(promiscuousCallback);
}

void loop() {
  // Process and send data over Serial from the buffer
  if (readIndex != writeIndex || bufferFull) {
    PacketData packet;

    noInterrupts();  // Temporarily disable interrupts to access shared variables
    memcpy(&packet, (void*)&packetBuffer[readIndex], sizeof(PacketData));
    readIndex = (readIndex + 1) % BUFFER_SIZE;
    bufferFull = false;
    interrupts();  // Re-enable interrupts

    // Send data over Serial
    Serial.print(packet.timestamp);
    Serial.print(":");
    Serial.println(packet.rssi);
  }
}
