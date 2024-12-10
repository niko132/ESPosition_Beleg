#ifndef DEBUG_H
#define DEBUG_H

#define DEBUG_PRINT(x) if (DEBUG) Serial.print(x)
#define DEBUG_PRINTLN(x) if (DEBUG) Serial.println(x)
#define DEBUG_PRINTF(...) if (DEBUG) Serial.printf(__VA_ARGS__)

#endif // DEBUG_H
