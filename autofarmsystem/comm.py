import serial
import time
import re

#Define serial port
# SERIAL_PORT = "/dev/serial0" # for raspberry pi
SERIAL_PORT = "COM3"  # Example: "COM3" (Windows) or "/dev/ttyUSB0" (Linux)
BAUD_RATE = 9600
ALLOWED_NOS = {
            "primary": "+917038835527",   # Primary Number
            "secondary": ["+919921776490", "+xxxxxxxx"]  # Example Secondary Numbers
        }


class SIM800L:
    def __init__(self, port,baud_rate, timeout = 1 ):
                """
        Initialize serial communication with SIM800L module.
        :param port: Serial port (e.g., /dev/serial0 for Raspberry Pi)
        :param baud_rate: Communication speed (default 9600)
        :param timeout: Time to wait for response
        """
        self.ser = serial.Serial(port, baud_rate, timeout=timeout)    

    def send_command(self, command, delay = 1):
                """
        Sends an AT command to the SIM800L module.
        :param command: AT command string (without '\r\n')
        :param wait: Time to wait for response (in seconds)
        :return: Response from the module
        """
        self.ser.write((command + "\r\n").encode())
        time.sleep(delay)
        response = self.ser.read(ser.inWating()).decode("utf-8")
        return respose.strip()

    def check_connection(self):
        """
        Sends AT command to check if the module is responding.
        :return: True if module responds with 'OK', else False
        """
        response = self.send_command("AT")
        return "OK" in response

    def get_signal_strength(self):
        """
        Gets signal strength from the module.
        :return: Signal strength in dBm
        """
        response = self.send_command("AT+CSQ")
        if "+CSQ" in response:
            _, values = response.split(":")
            strength, _ = values.strip().split(",")
            return int(strength) * 2 - 113  # Convert to dBm
        return None
    
    def get_caller_id(self):
                """
        Reads the caller ID when a call is received.
        Returns the phone number if found, else None.
        """
        response = self.send_command("AT+CLCC", wait=2)  # Get caller info
        match = re.search(r'"\+(\d+)"', response)
        return f"+{match.group(1)}" if match else None

        def send_sms(self, phone_number, message):
        """
        Sends an SMS only to an authorized number.
        """
        if phone_number not in [ALLOWED_NOS["primary"]] + ALLOWED_NOS["secondary"]:
            print(f"Unauthorized SMS attempt to {phone_number}")
            return "Error: Unauthorized number"

        self.send_command(f'AT+CMGS="{phone_number}"')
        time.sleep(0.5)
        self.ser.write((message + "\x1A").encode())  # \x1A = End of message
        time.sleep(3)
        response = self.ser.read(self.ser.inWaiting()).decode(errors='ignore')
        return response.strip()

    def read_sms(self, index):
            """
            Reads SMS at a specific index.
            Returns sender number & message text.
            """
            response = self.send_command(f"AT+CMGR={index}", wait=2)
            match = re.search(r'\+CMGR:.*?"(\+\d+)",.*?\n(.*)', response, re.DOTALL)
            if match:
                sender, message = match.groups()
                return sender.strip(), message.strip()
            return None, None

    def check_new_sms(self):
        """
        Checks for new unread SMS and processes authorized commands.
        """
        valid_messages = []

        response = self.send_command("AT+CMGL=\"REC UNREAD\"", wait=2)
        messages = re.findall(r'\+CMGL: (\d+),.*?"(\+\d+)",.*?\n(.*)', response, re.DOTALL)

        for index, sender, message in messages:
            sender = sender.strip()
            message = message.strip()
            
            if sender in [self.ALLOWED_NOS["primary"]] + self.ALLOWED_NOS["secondary"]:
                print(f"✅ Authorized SMS received from {sender}: {message}")
                valid_messages.append((sender, message))  # Forward to Raspberry Pi
            else:
                print(f"❌ Unauthorized SMS from {sender}: Ignored")
            
            # Delete the processed message to avoid re-processing
            self.send_at_command(f"AT+CMGD={index}")
# Test Connection
if __name__ == "__main__":
    print("Sending AT Command...")
    response = send_command("AT")  # Basic command to check communication
    print("Response:", response)




# #Basic AT Commands
# "AT"                # Check if SIM800L is responding (Returns: OK)
# "AT+GMR"           # Get module firmware version
# "AT+CFUN=1"        # Set full functionality mode
# "AT+CPIN?"         # Check SIM card status (Returns: READY if SIM is inserted)
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

