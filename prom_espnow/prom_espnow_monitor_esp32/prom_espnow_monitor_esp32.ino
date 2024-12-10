#include <Arduino.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>
#include "EspWifiTypes.h"

#define DEBUG false
#include "Debug.h"

#define QUEUE_SIZE 100 // about 5 are enough

/*
  METHOD DEFINITIONS
*/
void initWifi();

void getPacketSender(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf);
bool isTargetMac(const uint8_t *mac);
bool isMonitorMac(const uint8_t *mac);

void ICACHE_FLASH_ATTR promiscuousCallback(void *buf, wifi_promiscuous_pkt_type_t type);
void espNowDataSentCallback(const uint8_t *dstMac, esp_now_send_status_t status);
void sendRssiData(const packet_info& pi);

/*
  CONST VARIABLES
*/
const int WIFI_CHANNEL = 1;
const uint8_t MAC_ESP_NOW[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };

// List of target MAC addresses
const uint8_t TARGET_MACS[][6] = {
    { 0xDA, 0x9E, 0xC7, 0xF5, 0x5B, 0xEB },	// Google Pixel 9 Pro XL
    { 0x34, 0x2E, 0xB6, 0x1E, 0xC4, 0x46 },	// Huawei P20 Pro
    { 0x1A, 0x77, 0xA3, 0xF7, 0x43, 0x64 },	// Apple iPhone XR
};
const size_t TARGET_MAC_COUNT = sizeof(TARGET_MACS) / sizeof(TARGET_MACS[0]);

// List of monitor MAC addresses
const uint8_t MONITOR_MACS[][6] = {
  // ESP8266
  { 0x48, 0x3F, 0xDA, 0x46, 0x7E, 0x7A },
  { 0xD8, 0xBF, 0xC0, 0x11, 0x7C, 0x7D },
  { 0x24, 0xA1, 0x60, 0x2C, 0xCF, 0xAB },
  { 0xA4, 0xCF, 0x12, 0xFD, 0xAE, 0xA9 },

  // ESP32
  { 0xA0, 0xA3, 0xB3, 0xFF, 0x35, 0xC0 },
  { 0xF8, 0xB3, 0xB7, 0x34, 0x34, 0x7C },
  { 0xA0, 0xA3, 0xB3, 0xFF, 0x66, 0xB4 },
  { 0x08, 0xA6, 0xF7, 0xA1, 0xE5, 0xC8 },
  { 0xF8, 0xB3, 0xB7, 0x32, 0xFB, 0x6C },
  { 0xF8, 0xB3, 0xB7, 0x33, 0x03, 0xE8 }
};
const size_t MONITOR_MAC_COUNT = sizeof(MONITOR_MACS) / sizeof(MONITOR_MACS[0]);

/*
  GLOBAL VARIABLES
*/
QueueHandle_t queue;

void initWifi() {
  // init wifi
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();
  esp_wifi_set_channel(WIFI_CHANNEL, WIFI_SECOND_CHAN_NONE);

  // init esp now
  if (esp_now_init() != ESP_OK) {
    DEBUG_PRINTLN("Error initializing ESP-NOW");
    return;
  }
  esp_now_register_send_cb(espNowDataSentCallback);

  // add peer
  esp_now_peer_info_t peerInfo = {};
  memcpy(peerInfo.peer_addr, MAC_ESP_NOW, 6);
  peerInfo.channel = WIFI_CHANNEL;
  peerInfo.encrypt = false;
  if (esp_now_add_peer(&peerInfo) != ESP_OK) {
    DEBUG_PRINTLN("Failed to add peer");
  }

  // init promiscuous mode
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


void ICACHE_FLASH_ATTR promiscuousCallback(void *buf, wifi_promiscuous_pkt_type_t type) {
  wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buf;
  wifi_ieee80211_packet_t *ipkt = (wifi_ieee80211_packet_t *)ppkt->payload;
  int rssi = ppkt->rx_ctrl.rssi;
  uint8_t macSender[6];
  getPacketSender(ipkt, macSender);

  if (isTargetMac(macSender) || (isMonitorMac(macSender) && isTargetMac(&ipkt->payload[7]))) {
    packet_info pi;
    memcpy(pi.srcMac, macSender, 6);
    pi.rssi = (int8_t)rssi;
    xQueueSendFromISR(queue, &pi, NULL);
  }
}

void espNowDataSentCallback(const uint8_t *dstMac, esp_now_send_status_t status) {
  DEBUG_PRINT("ESP NOW: send to ");
  DEBUG_PRINTF(MACSTR, MAC2STR(dstMac));
  DEBUG_PRINTLN(status == 0 ? " successful" : " failed");
}

void sendRssiData(const packet_info& pi) {
  uint8_t buffer[7]; // 6 for mac + 1 for rssi
  memcpy(buffer, pi.srcMac, 6);
  buffer[6] = (uint8_t) -pi.rssi; // RSSI should be between [-100,0]

  DEBUG_PRINTF(MACSTR, MAC2STR(pi.srcMac));
  DEBUG_PRINTLN();

  esp_now_send((uint8_t*)MAC_ESP_NOW, buffer, sizeof(buffer));
}

void setup() {
  Serial.begin(115200);

  // required on ESP32 to get mac
  WiFi.mode(WIFI_STA);
  WiFi.STA.begin();
  DEBUG_PRINTLN();
  DEBUG_PRINTF("ESP32 Board MAC Address: %s\n", WiFi.macAddress().c_str());

  queue = xQueueCreate(QUEUE_SIZE, sizeof(packet_info));
  if (queue == NULL) {
    DEBUG_PRINTLN("Failed to create queue");
    return;
  }

  initWifi();
}

void loop() {
  packet_info pi;
  if (xQueueReceive(queue, &pi, 0) == pdTRUE) {
    sendRssiData(pi);
  }
}
