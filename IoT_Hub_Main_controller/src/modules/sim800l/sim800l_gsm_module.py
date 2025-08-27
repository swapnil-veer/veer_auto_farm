import os
import time
import re
import serial
import logging


from dotenv import load_dotenv
logger = logging.getLogger(__name__)

load_dotenv()

ph_no_1 = os.getenv("ph_no_1")
ph_no_2 = os.getenv("ph_no_2")

# Define serial port
SERIAL_PORT = "/dev/serial0"  # for raspberry pi
# SERIAL_PORT = "COM3"  # Example: "COM3" (Windows) or "/dev/ttyUSB0" (Linux)
BAUD_RATE = 9600


class SIM800L:
    """Class for SIM800L GSM Module operations"""

    ALLOWED_NOS = {
        "admin": ph_no_1,  # admin Number
        "secondary": ph_no_2,  # Example Secondary Numbers
    }

    def __init__(self, port=SERIAL_PORT, baud_rate=BAUD_RATE, timeout=1):
        """
        Initialize serial communication with SIM800L module.
        :param port: Serial port (e.g., /dev/serial0 for Raspberry Pi)
        :param baud_rate: Communication speed (default 9600)
        :param timeout: Time to wait for response
        """
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=timeout)
            logger.info(f"Connected to SIM800L on {port} at {baud_rate} baud.")
        except serial.SerialException as e:
            logger.error(f"Failed to initialize SIM800L: {e}")
            return None

    def send_command(self, command, delay=1):
        """
        Sends an AT command to the SIM800L module.
        :param command: AT command string (without '\r\n')
        :param wait: Time to wait for response (in seconds)
        :return: Response from the module
        """
        try:
            self.ser.write((command + "\r\n").encode())
            time.sleep(delay)
            response = self.ser.read(self.ser.inWaiting()).decode("utf-8")
            logger.debug(f"Command: {command} | Response: {response.strip()}")
            return response.strip()
        except Exception as e:
            logger.error(f"failing to sending command '{command}': {e}")
            return None

    def check_connection(self):
        """
        Sends AT command to check if the module is responding.
        :return: True if module responds with 'OK', else False
        """
        response = self.send_command("AT")
        if response and "OK" in response:
            logger.info("SIM800L is responding.")
            return True
        else:
            logger.warning("SIM800L is not responding.")
            return False

    def get_signal_strength(self):
        """
        Gets signal strength from the module.
        :return: Signal strength in dBm
        """
        response = self.send_command("AT+CSQ")
        if "+CSQ" in response:
            _, values = response.split(":")
            strength, _ = values.strip().split(",")
            dBm = int(strength) * 2 - 113
            logger.info(f"Signal strength: {dBm} dBm")
            return dBm  # Convert to dBm
        logger.warning("Failed to get signal strength.")
        return None

    def get_caller_id(self):
        """
        Reads the caller ID when a call is received.
        Returns the phone number if found, else None.
        """
        response = self.send_command("AT+CLCC", delay=2)  # Get caller info
        match = re.search(r'"\+(\d+)"', response)
        caller_id = f"+{match.group(1)}" if match else None
        if caller_id:
            logger.info(f"Incoming call from {caller_id}")
        else:
            logger.warning("Caller ID not found.")
        return caller_id

    def send_sms(self, phone_number, message):
        """
        Sends an SMS only to an authorized number.
        """
        if phone_number not in (
            [self.ALLOWED_NOS["admin"]] or self.ALLOWED_NOS["secondary"]
        ):
            logger.warning(f"Unauthorized SMS attempt to {phone_number}")
            return "Error: Unauthorized number"

        logger.info(f"Sending SMS to {phone_number}: {message}")
        self.send_command(f'AT+CMGS="{phone_number}"')
        time.sleep(0.5)
        self.ser.write((message + "\x1a").encode())  # \x1A = End of message
        time.sleep(3)
        response = self.ser.read(self.ser.inWaiting()).decode(errors="ignore")
        logger.debug(f"SMS Response: {response.strip()}")
        return response.strip()

    def read_sms(self, index):
        """
        Reads SMS at a specific index.
        Returns sender number & message text.
        """
        response = self.send_command(f"AT+CMGR={index}", delay=2)
        match = re.search(r'\+CMGR:.*?"(\+\d+)",.*?\n(.*)', response, re.DOTALL)
        if match:
            sender, message = match.groups()
            logger.info(f"Read SMS from {sender}: {message}")
            return sender.strip(), message.strip()
        logger.warning(f"No SMS found at index {index}.")
        return None, None

    def check_new_sms(self):
        """
        Checks for new unread SMS and processes authorized commands.
        """
        valid_messages = []

        response = self.send_command('AT+CMGL=\"ALL\"', delay=2)
        messages = re.findall(
            r'\+CMGL: (\d+),.*?"(\+\d+)",.*?\n(.*)', response, re.DOTALL
        )

        for index, sender, message in messages:
            sender = sender.strip()
            message = message.strip()

            if sender in self.ALLOWED_NOS.values():
                logger.info(f"Authorized SMS received from {sender}: {message}")
                # {index: "", sender : "", message = "'"}
                temp_dict= {}
                temp_dict["sender"] = sender
                temp_dict["index"] = index
                temp_dict["msg"] = message
                valid_messages.append(temp_dict)

                # valid_messages[sender]= message  # Forward to Raspberry Pi
            else:
                logger.info(f"Unauthorized SMS from {sender}: Ignored")

            # Delete the processed message to avoid re-processing
            self.send_command(f"AT+CMGD={index}")
        return valid_messages



# Test Connection
if __name__ == "__main__":
    print("Sending AT Command...")
    a = SIM800L()
    response = a.send_command("AT")  # Basic command to check communication
    print("Response:", response)


# #Basic AT Commands
# "AT"                # Check if SIM800L is responding (Returns: OK)
# "AT+GMR"           # Get module firmware version
# "AT+CFUN=1"        # Set full functionality mode
# "AT+CPIN?"        # Check SIM card status (Returns: READY if SIM is inserted)
# "AT+CSQ"           # Check signal strength (Returns: +CSQ: <rssi>,<ber>)
# "AT+COPS?"         # Get current network operator
# "AT+CREG?"         # Check network registration status

# SMS Commands
# "AT+CMGF=1"               # Set SMS mode to text
# "AT+CMGS=\"+919876543210\""  # Send SMS (Enter text, then Ctrl+Z to send)
# "AT+CMGR=1"               # Read SMS from memory (1st slot)
# "AT+CMGL=\"ALL\""         # List all messages
# "AT+CMGD=1"               # Delete SMS at memory location 1

# Call Commands
# "ATD+919876543210;"       # Dial a number
# "ATA"                     # Answer an incoming call
# "ATH"                     # Hang up call
# "AT+CLCC"                 # Get current call status
# "AT+COLP=1"               # Enable caller ID
# "AT+VTS=1"                # Send DTMF tone (1-9, *, #)

# Network & GPRS Commands
# "AT+COPS?"                # Get current network operator
# "AT+CGATT?"               # Check if GPRS is attached (Returns: 1 if connected)
# "AT+CSTT=\"internet\""    # Set APN (Change "internet" to your provider's APN)
# "AT+CIICR"                # Activate wireless connection
# "AT+CIFSR"                # Get local IP address
# "AT+CIPSTATUS"            # Get connection status
# "AT+CIPSTART=\"TCP\",\"example.com\",\"80\""  # Start TCP connection
# "AT+CIPSEND"              # Send data (Enter data, then Ctrl+Z)
# "AT+CIPCLOSE"             # Close connection
# "AT+CIPSHUT"              # Shut down GPRS connection

# Power Management
# "AT+CPOWD=1"              # Turn off module
# "AT+CFUN=0"               # Minimum functionality mode (low power)
# "AT+CFUN=1"               # Full functionality mode
# "AT+CSCLK=1"              # Enable sleep mode
# "AT+CSCLK=0"              # Disable sleep mode
