#include <ESP8266WiFi.h>
#include <espnow.h>

/*
  METHOD DEFINITIONS
*/
void initWifi();
void printMacString(const uint8_t *mac);
void espNowDataReceivedCallback(const uint8_t *srcMac, const uint8_t *incomingData, int len);

/*
  CONST VARIABLES
*/
const int WIFI_CHANNEL = 1;

// !!!!!!!!!!!!!!!!!!!!
// THIS DEVICES MAC IS
// 48:3F:DA:46:7E:7A
// !!!!!!!!!!!!!!!!!!!!

void initWifi() {
  // init wifi
  wifi_set_opmode(STATION_MODE);
  wifi_set_channel(WIFI_CHANNEL);

  // init esp now
  esp_now_init();
  esp_now_register_recv_cb(esp_now_recv_cb_t(espNowDataReceivedCallback));
}

void printMacString(const uint8_t *mac) {
  Serial.printf("%02x%02x%02x%02x%02x%02x", mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

void espNowDataReceivedCallback(const uint8_t *srcMac, const uint8_t *incomingData, int len) {
  // our packets are always 7 bytes
  if (len != 7)
    return;

  uint8_t targetMac[6];
  int rssi;

  memcpy(targetMac, incomingData, 6);
  rssi = -incomingData[6]; // RSSI is transmitted as signed byte

  printMacString(srcMac);
  Serial.print("_");
  printMacString(targetMac);
  Serial.printf(":%d\n", rssi);
}


void setup() {
  Serial.begin(115200);

  Serial.println();
  Serial.print("ESP Board MAC Address:  ");
  Serial.println(WiFi.macAddress());

  initWifi();
}

void loop() {

}