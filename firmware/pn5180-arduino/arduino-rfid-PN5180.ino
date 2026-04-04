/**
 * PN5180 ISO15693 RFID reader(s) — machine-parseable serial output for ROS 2.
 *
 * Output format (one line per event, 115200 baud):
 *   R<reader_index>,<hex_uid>   tag present (e.g. R0,E00401005E231B26)
 *   X<reader_index>             tag removed from reader
 *
 * Change NUM_READERS and the nfc[] constructors to match your wiring.
 */

#include "PN5180-Library/PN5180.h"
#include "PN5180-Library/PN5180ISO15693.h"

// Number of PN5180 readers (expand nfc[] and pin lists when > 1)
static const byte NUM_READERS = 1;

PN5180ISO15693 nfc[NUM_READERS] = {
  PN5180ISO15693(2, 15, 0),  // NSS, BUSY, RESET — adjust per board
};

uint8_t lastUid[NUM_READERS][8];

void printHexUidUpper(uint8_t *uid, size_t len) {
  for (size_t j = 0; j < len; j++) {
    if (uid[j] < 16) {
      Serial.print('0');
    }
    Serial.print(uid[j], HEX);
  }
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_READERS; i++) {
    nfc[i].begin();
    nfc[i].reset();
    nfc[i].setupRF();
    memset(lastUid[i], 0, sizeof(lastUid[i]));
  }
  Serial.println(F("READY"));
}

void loop() {
  for (int i = 0; i < NUM_READERS; i++) {
    uint8_t thisUid[8];
    ISO15693ErrorCode rc = nfc[i].getInventory(thisUid);

    if (rc == ISO15693_EC_OK) {
      if (memcmp(thisUid, lastUid[i], 8) == 0) {
        continue;
      }
      memcpy(lastUid[i], thisUid, sizeof(thisUid));
      Serial.print(F("R"));
      Serial.print(i);
      Serial.print(F(","));
      printHexUidUpper(thisUid, sizeof(thisUid));
      Serial.println();
    } else {
      if (lastUid[i][7] == 0xE0) {
        Serial.print(F("X"));
        Serial.println(i);
        memset(lastUid[i], 0, sizeof(lastUid[i]));
      }
    }
    delay(10);
  }
}
