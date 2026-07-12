# hardware/sim_modem.py
import gammu
from logging_config import logger

class SIMModem:
    def __init__(self):
        self.sm = gammu.StateMachine()
        # self.sm.ReadConfig()
        self.sm.SetConfig(
            0,
            {
                "Device": "/dev/serial0",
                "Connection": "at9600"
            }
        )
        self.connected = False
        self.init()

    def init(self):
        try:
            self.sm.Init()
            self.connected = True
            logger.info("SIM modem connected")
        except Exception as e:
            self.connected = False
            logger.error(f"SIM init failed: {e}")

    def check_connection(self) -> bool:
        try:
            self.sm.GetSIMIMSI()
            self.connected = True
        except Exception:
            self.connected = False
        return self.connected

    def get_signal_strength(self):
        if not self.connected:
            return None
        try:
            return self.sm.GetSignalQuality()["SignalPercent"]
        except Exception:
            self.connected = False
            return None

    def read_all_sms(self):
        sms_list = []
        start = True
        cursms = None

        try:
            status = self.sm.GetSMSStatus()
            remain = (
                status.get("SIMUsed", 0)
                + status.get("PhoneUsed", 0)
                + status.get("TemplatesUsed", 0)
            )
            if remain > 0:
                logger.info("SMS status fetched successfully. Remaining messages: %s", remain)

            while remain > 0:
                try:
                    if start:
                        cursms = self.sm.GetNextSMS(Start=True, Folder=0)
                        start = False
                    else:
                        cursms = self.sm.GetNextSMS(
                            Location=cursms[0]["Location"],
                            Folder=0
                        )

                    if not cursms:
                        logger.info("No more SMS returned by device.")
                        break

                    remain -= len(cursms)
                    sms_list.append(cursms)

                    logger.debug(
                        "Fetched %s SMS part(s). Remaining counter: %s",
                        len(cursms),
                        remain
                    )

                except gammu.ERR_EMPTY:
                    logger.info("SMS storage is empty or no more SMS available.")
                    break
                except gammu.GSMError as e:
                    logger.exception(
                        "Gammu error while reading SMS batch: %s",
                        getattr(e, "Text", str(e))
                    )
                    raise

            if not sms_list:
                return []

            linked_sms = gammu.LinkSMS(sms_list)
            logger.info("Successfully linked %s SMS record(s).", len(linked_sms))
            return linked_sms

        except gammu.GSMError as e:
            logger.exception(
                "Failed to fetch SMS from device: %s",
                getattr(e, "Text", str(e))
            )
            return []
        except KeyError as e:
            logger.exception("Unexpected SMS/status structure from Gammu: missing key %s", e)
            return []
        except Exception:
            logger.exception("Unexpected error while fetching SMS")
            return []
    
    def delete_sms(self, folder, location):
        try:
            self.sm.DeleteSMS(folder, location)
            return True
        except Exception as e:
            logger.error(f"Delete failed {folder}:{location}: {e}")
            return False

    def send_sms(self, number, text):
        msg = {
        "Text": text,
        "SMSC": {"Location": 1},
        "Number": number,
        }
        # self.sm.SendSMS(msg)
        try:
            self.sm.SendSMS(msg)
            logger.info("SMS sent successfully to %s", number)
            return True

        except gammu.GSMError as e:
            logger.exception(
                "Gammu failed to send SMS to %s: %s",
                number,
                getattr(e, "Text", str(e))
            )
            raise

        except Exception:
            logger.exception("Unexpected error while sending SMS to %s", number)
            raise