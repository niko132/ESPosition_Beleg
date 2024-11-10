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
bool macEquals(const uint8_t *mac1, const uint8_t *mac2);
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

bool macEquals(const uint8_t *mac1, const uint8_t *mac2) {
    return memcmp(mac1, mac2, 6) == 0;
}

void printMac(const uint8_t *mac) {
    Serial.printf("%02x:%02x:%02x:%02x:%02x:%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void promiscuousCallback(void *buf, wifi_promiscuous_pkt_type_t type) {
    wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buf;
    wifi_ieee80211_packet_t *ipkt = (wifi_ieee80211_packet_t *)ppkt->payload;
    int rssi = ppkt->rx_ctrl.rssi;
    uint8_t macSender[6];
    getPacketSender(ipkt, macSender);

    if (!macEquals(macSender, MAC_POS_TARGET))
        return;

    memcpy(lastMac, macSender, 6);
    lastRssi = rssi;
    isDirty = true;
}

void espNowDataSentCallback(const uint8_t *macAddr, esp_now_send_status_t status) {
    Serial.print("ESP NOW: send to ");
    printMac(macAddr);
    Serial.println(status == ESP_NOW_SEND_SUCCESS ? " successful" : " failed");
}

void sendRssiData() {
    uint8_t buffer[7]; // 6 for mac + 1 for rssi
    memcpy(buffer, lastMac, 6);
    buffer[6] = (uint8_t) -lastRssi; // RSSI should be between [-100,0]

    esp_now_send(MAC_ESP_NOW, buffer, sizeof(buffer));
}

void setup() {
    Serial.begin(115200);
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
