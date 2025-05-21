# veer_auto_farm
# Raspberry Pi-Based Auto Farm System

## Overview

This project is a **GSM/GPRS-controlled auto farm system** built using a **Raspberry Pi Zero 2 W**. The system automates motor control and monitors bypass mode, dry-run conditions, and phase availability using relays and sensors. It also includes an LCD display for real-time status updates.

## Hardware Components

- **Raspberry Pi Zero 2 W** – Main microcontroller
- **SIM800L** – GSM/GPRS module for remote control
- **ZMCT103C + ADS1115** – AC current sensor for dry-run detection
- **DPST Switch** – For detecting bypass mode
- **SRD-05VDC-SL-C Relays (2x)** – For motor on/off control and dry-run protection
- **Phase Monitoring Module** – Detects phase loss and faults
- **LCD (I2C)** – Displays system status
- **Power Setup**:
  - AC-DC Adapter (12V, 3A)
  - Li-Ion Batteries (4x DMEGC INR18650-26E)
  - BMS (2S 20A)
  - DC-DC Step Down (XL4015 - 5V, 4.2V, 12V)

## Wiring Diagram

![alt text](schematic/auto-farm-schematic.png)

### Key GPIO Connections:

| Component                                  | GPIO Pin                 |
| ------------------------------------------ | ------------------------ |
| **LCD (I2C)**                              | SDA (BCM 2), SCL (BCM 3) |
| **ZMCT103C + ADS1115**                     | I2C (SDA, SCL)           |
| **Bypass Mode Detection (DPST Switch)**    | GPIO 23                  |
| **Dry-Run Relay**                          | GPIO 18                  |
| **Pi On/Off Relay**                        | GPIO 16                  |
| **Phase Monitor - Green (OK)**             | GPIO 11                  |
| **Phase Monitor - Yellow (Initial Wait)**  | GPIO 13                  |
| **Phase Monitor - Red (Fault/Phase Loss)** | GPIO 15                  |

## Setup Instructions

1. Clone the repository:
   ```sh
   git clone https://github.com/veer_auto_farm.git
   cd your-repo-name
   ```
2. Install dependencies:
   ```sh
   sudo apt update && sudo apt install python3-pip
   pip3 install RPi.GPIO smbus2 adafruit-circuitpython-ads1x15
   ```
3. Connect hardware as per the Fritzing schematic.
4. Run the main script:
   ```sh
   python3 main.py
   ```

## How It Works

- **Bypass Mode Detection**: A DPST switch changes state when the motor is manually turned on, and the Raspberry Pi detects it via GPIO 23.
- **Dry-Run Detection**: ZMCT103C AC current sensor (with ADS1115) checks if the motor draws current. If no current is detected, the motor is in dry-run mode.
- **Phase Monitoring**: The phase monitor module checks for faults and missing phases, updating GPIO states accordingly.
- **Motor Control**: The system controls relays connected to GPIO 16 (Pi On/Off Relay) and GPIO 18 (Dry-Run Relay) to automate motor operations.
- **LCD Display**: Displays real-time system status.

## Future Improvements

- **Optimize power consumption**
- **Add logging and remote monitoring**
- **Enhance GSM module communication**

---

### Contributors

- **Swapnil Sanjay Veer** – Project Lead

### License

This project is licensed under the MIT License.

