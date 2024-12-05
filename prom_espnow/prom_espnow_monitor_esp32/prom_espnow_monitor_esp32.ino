#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

/*
  TYPE DEFINITIONS
*/
typedef struct {
    unsigned frame_ctrl:16;
    unsigned duration_id:16;
    uint8_t addr1[6]; /* receiver address */
    uint8_t addr2[6]; /* sender address */
    uint8_t addr3[6]; /* filtering address */
    unsigned sequence_ctrl:16;
    uint8_t addr4[6]; /* optional */
} wifi_ieee80211_mac_hdr_t;

typedef struct {
    wifi_ieee80211_mac_hdr_t hdr;
    uint8_t payload[0]; /* network data ended with 4 bytes csum (CRC32) */
} wifi_ieee80211_packet_t;

typedef struct {
    uint8_t srcMac[6];
    double rssiSum;
    size_t rssiCnt;
} rssi_aggregation;

/*
  METHOD DEFINITIONS
*/
void initWifi();
void getPacketSender(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf);
bool isTargetMac(const uint8_t *mac);
bool isMonitorMac(const uint8_t *mac);
void printMac(const uint8_t *mac);

void promiscuousCallback(void *buf, wifi_promiscuous_pkt_type_t type);
void espNowDataSentCallback(const uint8_t *macAddr, esp_now_send_status_t status);
void sendRssiData();

/*
  CONST VARIABLES
*/
const int WIFI_CHANNEL = 1;
const uint8_t MAC_ESP_NOW[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
const uint8_t MAC_POS_TARGET[] = { 0xDA, 0x9E, 0xC7, 0xF5, 0x5B, 0xEB };

// List of target MAC addresses
const uint8_t TARGET_MACS[][6] = {
    { 0xDA, 0x9E, 0xC7, 0xF5, 0x5B, 0xEB },
    { 0x34, 0x2e, 0xb6, 0x1e, 0xc4, 0x46 }
};
const size_t TARGET_MAC_COUNT = sizeof(TARGET_MACS) / sizeof(TARGET_MACS[0]);

// List of monitor MAC addresses
const uint8_t MONITOR_MACS[][6] = {
    { 0xA0, 0xA3, 0xB3, 0xFF, 0x35, 0xC0 },
    { 0xF8, 0xB3, 0xB7, 0x34, 0x34, 0x7C },
    { 0xA0, 0xA3, 0xB3, 0xFF, 0x66, 0xB4 },
    { 0x24, 0x62, 0xAB, 0xFB, 0x15, 0xA8 }
};
const size_t MONITOR_MAC_COUNT = sizeof(MONITOR_MACS) / sizeof(MONITOR_MACS[0]);

/*
  GLOBAL VARIABLES
*/
uint8_t lastMac[6];
int lastRssi = 0;
bool isDirty = false;

void initWifi() {
    // Init WiFi
    WiFi.mode(WIFI_STA);
    WiFi.disconnect();
    esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);

    // Init ESP-NOW
    if (esp_now_init() != ESP_OK) {
        Serial.println("Error initializing ESP-NOW");
        return;
    }
    esp_now_register_send_cb(espNowDataSentCallback);

    // Add peer
    esp_now_peer_info_t peerInfo = {};
    memcpy(peerInfo.peer_addr, MAC_ESP_NOW, 6);
    peerInfo.channel = WIFI_CHANNEL;
    peerInfo.encrypt = false;
    if (esp_now_add_peer(&peerInfo) != ESP_OK) {
        Serial.println("Failed to add peer");
    }

    // Init promiscuous mode
    esp_wifi_set_promiscuous(true);
    esp_wifi_set_promiscuous_rx_cb(promiscuousCallback);
}

void getPacketSender(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf) {
    memcpy(macBuf, ipkt->hdr.addr2, 6);
}

bool isTargetMac(const uint8_t *mac) {
    for (size_t i = 0; i < TARGET_MAC_COUNT; i++) {
        if (memcmp(mac, TARGET_MACS[i], 6) == 0) {
            return true;
        }
    }
    return false;
}

bool isMonitorMac(const uint8_t *mac) {
    for (size_t i = 0; i < MONITOR_MAC_COUNT; i++) {
        if (memcmp(mac, MONITOR_MACS[i], 6) == 0) {
            return true;
        }
    }
    return false;
}

void printMac(const uint8_t *mac) {
    Serial.printf("%02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static void printBufferHexAndASCII(uint8_t* buffer, size_t length) {
    printf("Buffer (length %zu bytes):\n", length);

    // Print Hexadecimal values
    for (size_t i = 0; i < length; i++) {
        printf("%02X ", buffer[i]); // Print byte as two-digit hexadecimal
        if ((i + 1) % 16 == 0 || i == length - 1) {
            // Add padding if it's the last line and less than 16 bytes
            if (i == length - 1) {
                size_t padding = (16 - ((i + 1) % 16)) % 16;
                for (size_t j = 0; j < padding; j++) {
                    printf("   "); // Add spaces for alignment
                }
            }
            printf(" | ");

            // Print ASCII representation for the current row
            size_t start = i / 16 * 16; // Row start index
            size_t end = (i + 1); // Row end index
            for (size_t j = start; j < end; j++) {
                if (isprint(buffer[j])) {
                    printf("%c", buffer[j]); // Printable ASCII character
                } else {
                    printf("."); // Non-printable character as '.'
                }
            }
            printf("\n");
        }
    }
}

void promiscuousCallback(void *buf, wifi_promiscuous_pkt_type_t type) {
    wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buf;
    wifi_ieee80211_packet_t *ipkt = (wifi_ieee80211_packet_t *)ppkt->payload;
    int rssi = ppkt->rx_ctrl.rssi;
    uint8_t macSender[6];
    getPacketSender(ipkt, macSender);

    if (isTargetMac(macSender)) {
      memcpy(lastMac, macSender, 6);
      lastRssi = rssi;
      isDirty = true;
    }

    if (isMonitorMac(macSender)) {
      // check the origin mac of that message to stop bouncing of monitor messages
      uint8_t* targetMac = &ipkt->payload[7];
      if (!isTargetMac(targetMac)) {
        return;
      }

      memcpy(lastMac, macSender, 6);
      lastRssi = rssi;
      isDirty = true;
    }
}

void espNowDataSentCallback(const uint8_t *macAddr, esp_now_send_status_t status) {
    /*
    Serial.print("ESP NOW: send to ");
    printMac(macAddr);
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? " successful" : " failed");
    */
}

void printMac1(const uint8_t *mac) {
    Serial.printf("%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void sendRssiData() {
    uint8_t buffer[7]; // 6 for mac + 1 for rssi
    memcpy(buffer, lastMac, 6);
    buffer[6] = (uint8_t) -lastRssi; // RSSI should be between [-100,0]

    esp_now_send(MAC_ESP_NOW, buffer, sizeof(buffer));

    printMac1(lastMac);
    Serial.printf(":%d\n", lastRssi);
}

void setup() {
    Serial.begin(115200);

    // required on ESP32 to get mac
    WiFi.mode(WIFI_STA);
    WiFi.STA.begin();
    Serial.println();
    Serial.printf("ESP32 Board MAC Address: %s\n", WiFi.macAddress().c_str());
    initWifi();
}

void loop() {
    if (isDirty) {
        sendRssiData();
        isDirty = false;
    }
}
