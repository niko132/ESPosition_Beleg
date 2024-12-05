#include <Arduino.h>
#include <ESP8266WiFi.h>
#include <espnow.h>

extern "C" {
  #include <user_interface.h>
}

/*
  TYPE DEFINITIONS
*/
typedef struct {
	signed rssi: 8;
	unsigned rate: 4;
	unsigned is_group: 1;
	unsigned: 1;
	unsigned sig_mode: 2;
	unsigned legacy_length: 12;
	unsigned damatch0: 1;
	unsigned damatch1: 1;
	unsigned bssidmatch0: 1;
	unsigned bssidmatch1: 1;
	unsigned MCS: 7;
	unsigned CWB: 1;
	unsigned HT_length: 16;
	unsigned Smoothing: 1;
	unsigned Not_Sounding: 1;
	unsigned: 1;
	unsigned Aggregation: 1;
	unsigned STBC: 2;
	unsigned FEC_CODING: 1;
	unsigned SGI: 1;
	unsigned rxend_state: 8;
	unsigned ampdu_cnt: 8;
	unsigned channel: 4;
	unsigned: 12;
} wifi_pkt_rx_ctrl_t;

typedef struct {
	wifi_pkt_rx_ctrl_t rx_ctrl;
	uint8_t payload[0]; /* ieee80211 packet buff */
} wifi_promiscuous_pkt_t;

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
bool isTargetMac(uint8_t *mac);

void ICACHE_FLASH_ATTR promiscuousCallback(uint8_t *buffer, uint16_t type);
void espNowDataSentCallback(uint8_t *dstMac, uint8_t sendStatus);
void sendRssiData();

/*
  CONST VARIABLES
*/
const int WIFI_CHANNEL = 1;
const uint8_t MAC_ESP_NOW[] = { 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF };
const int NUMBER_OF_TARGETS = 2;
const uint8_t MAC_POS_TARGETS[NUMBER_OF_TARGETS][6] = {
  { 0x34, 0x2E, 0xB6, 0x1E, 0xC4, 0x46 },
  { 0xDA, 0x9E, 0xC7, 0xF5, 0x5B, 0xEB }
};

/*
  GLOBAL VARIABLES
*/
uint8_t lastMac[6];
int lastRssi = 0;
bool isDirty = false;

void initWifi() {
  // init wifi
  wifi_set_opmode(STATION_MODE);
  wifi_set_channel(WIFI_CHANNEL);
  wifi_promiscuous_enable(0);

  // init esp now
  esp_now_init();
  esp_now_set_self_role(ESP_NOW_ROLE_CONTROLLER);
  esp_now_register_send_cb(esp_now_send_cb_t(espNowDataSentCallback));
  esp_now_add_peer((uint8_t*)MAC_ESP_NOW, ESP_NOW_ROLE_SLAVE, 1, NULL, 0);

  // init promiscuous mode
  wifi_set_promiscuous_rx_cb(promiscuousCallback);
  wifi_promiscuous_enable(1);
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

bool isTargetMac(uint8_t *mac) {
  for (int i = 0; i < NUMBER_OF_TARGETS; i++) {
    if (macEquals(mac, MAC_POS_TARGETS[i]))
      return true;
  }

  return false;
}


void ICACHE_FLASH_ATTR promiscuousCallback(uint8_t *buffer, uint16_t type) {
  const wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buffer;
  const wifi_ieee80211_packet_t *ipkt = (wifi_ieee80211_packet_t *)ppkt->payload;
  int rssi = ppkt->rx_ctrl.rssi;
  uint8_t macSender[6];
  getPacketSender(ipkt, macSender);

  if (!isTargetMac(macSender))
    return;
  
  memcpy(lastMac, macSender, 6);
  lastRssi = rssi;

  if (isDirty == true) {
    Serial.println("Missed packet");
  }

  isDirty = true;
}

void espNowDataSentCallback(uint8_t *dstMac, uint8_t sendStatus) {
  Serial.print("ESP NOW: send to ");
  printMac(dstMac);
  Serial.println(sendStatus == 0 ? " successful" : " failed");
}

void sendRssiData() {
  uint8_t buffer[7]; // 6 for mac + 1 for rssi
  memcpy(buffer, lastMac, 6);
  buffer[6] = (uint8_t) -lastRssi; // RSSI should be between [-100,0]

  esp_now_send((uint8_t*)MAC_ESP_NOW, buffer, sizeof(buffer));
}


void setup() {
  Serial.begin(115200);
  
  Serial.println();
  Serial.printf("ESP Board MAC Address: %s\n", WiFi.macAddress().c_str());

  initWifi();
}

void loop() {
  if (isDirty) {
    sendRssiData();
    isDirty = false;
  }
}