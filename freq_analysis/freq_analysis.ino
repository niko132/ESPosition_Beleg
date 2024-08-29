#include <Arduino.h>
#include <ESP8266WiFi.h>
extern "C" {
  #include <user_interface.h>
}

#define MAX_PACKETS 1000

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

// Structure to hold packet information
typedef struct {
  unsigned long timestamp;
  int rssi;
} PacketInfo;

/*
  METHOD DEFINITIONS
*/
void initWifi();

void getPacketSender(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf);
bool macEquals(const uint8_t *mac1, const uint8_t *mac2);

void ICACHE_FLASH_ATTR promiscuousCallback(uint8_t *buffer, uint16_t type);

/*
  CONST VARIABLES
*/
const int WIFI_CHANNEL = 6;
const uint8_t TARGET_MAC[] = { 0x34, 0x2e, 0xb6, 0x1e, 0xc4, 0x46 };
const unsigned long DURATION_MILLIS = 1 * 60 * 1000; // 1min

/*
  GLOBAL VARIABLES
*/
// Array to store packet information
PacketInfo packets[MAX_PACKETS];
unsigned int packetCount = 0;
// Start time for capturing packets
unsigned long startMillis;
bool isRunning = false;

void initWifi() {
  // init wifi
  wifi_set_opmode(STATION_MODE);
  wifi_set_channel(WIFI_CHANNEL);
  wifi_promiscuous_enable(0);

  // init promiscuous mode
  wifi_set_promiscuous_rx_cb(promiscuousCallback);
  wifi_promiscuous_enable(1);
}


void getPacketSender(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf) {
	const wifi_ieee80211_mac_hdr_t *hdr = &ipkt->hdr;
  memcpy(macBuf, hdr->addr2, 6);
}

bool macEquals(const uint8_t *mac1, const uint8_t *mac2) {
  return memcmp(mac1, mac2, 6) == 0;
}


void ICACHE_FLASH_ATTR promiscuousCallback(uint8_t *buffer, uint16_t type) {
  unsigned long nowMillis = millis();

  if (!isRunning || packetCount >= MAX_PACKETS)
    return;

  const wifi_promiscuous_pkt_t *ppkt = (wifi_promiscuous_pkt_t *)buffer;
  const wifi_ieee80211_packet_t *ipkt = (wifi_ieee80211_packet_t *)ppkt->payload;
  int rssi = ppkt->rx_ctrl.rssi;
  uint8_t senderMac[6];
  getPacketSender(ipkt, senderMac);

  if (!macEquals(senderMac, TARGET_MAC))
    return;
  
  packets[packetCount].timestamp = nowMillis;
  packets[packetCount].rssi = rssi;
  packetCount++;
}


void setup() {
  Serial.begin(115200);
  Serial.println();

  initWifi();

  Serial.printf("Press any key to start monitoring (%ds)\n", DURATION_MILLIS / 1000);
}

void loop() {
  unsigned long nowMillis = millis();

  if (!isRunning && Serial.available() > 0) {
    while (Serial.available() > 0) {
      Serial.readString();
    }
    startMillis = nowMillis;
    isRunning = true;
  }

  if (isRunning && nowMillis - startMillis >= DURATION_MILLIS) {
    // Send captured data over serial
    Serial.printf("Timestamp,RSSI\n");
    for (int i = 0; i < packetCount; i++) {
      Serial.printf("%lu,%d\n", packets[i].timestamp, packets[i].rssi);
    }

    packetCount = 0;  // Reset packet count
    isRunning = false;
  }
}