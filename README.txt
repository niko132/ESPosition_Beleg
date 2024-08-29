esposition_esp8266:
- example with promiscuous mode + kalman filter + ESPNOW sender

prom_espnow_monitor:
- in combination with prom_espnow_main
- send RSSI of every received packet over ESPNOW to a predefined main node

prom_espnow_main:
- in combination with prom_espnow_monitor
- implementation of a main node that just prints the MAC and RSSI of every packet

freq_analysis:
- code for finding the packet frequencies of a device in different (power-) states
- creates a CSV output
- contains python scripts to create plots of the data

methods_increase_packet_frequency:
	rts_cts_test:
	- test sending of RTS frames using wifi_send_pkt_freedom

	esp32-open-mac:
	- alternative stack implementation -> tried to send RTS frames but no effect


TODO:

- script for sending frequency analysis for different (power-) states - done
- script for increasing frequency using common SSIDs
- script for increasing frequency using known SSIDs
- script for increasing frequency using RTS frames - done -> not working
- script for ESPosition monitor (ESP8266)
- script for ESPosition monitor (ESP32)
- script for ESPosition main (trilateration; multilateration; ...)
- script for ESPosition main (fingerprinting)
- variable sending intervals (after every packet; after N packets; every T seconds)
- variable aggregation methods (send every; only newest; mean, median, kalman filter)
- extend ESPosition main with active monitor feedback