# Raspberry Pi Zero 2 W Setup & Recovery Guide

## Veer Auto Farm — Pump Controller

> **Purpose:** This document prepares the Raspberry Pi OS and all required system-level interfaces/access methods. It does not deploy or test the Veer Auto Farm application.
>


---

## Table of Contents

1. [System Overview](#system-overview)
2. [Hardware Requirements](#hardware-requirements)
3. [Prerequisites](#prerequisites)
4. [Raspberry Pi Imager](#raspberry-pi-imager)
5. [First Boot](#first-boot)
6. [Basic System Configuration](#basic-system-configuration)
7. [Raspberry Pi Configuration Tool](#raspberry-pi-configuration-tool)
8. [Raspberry Pi Connect](#raspberry-pi-connect)
9. [USB Gadget — Emergency Network Access](#usb-gadget--emergency-network-access)
10. [Network Verification](#network-verification)


---

# System Overview

The Veer Auto Farm Pump Controller uses a Raspberry Pi Zero 2 W as the main controller.

### Connectivity

```text
                         ┌─────────────────────┐
                         │ Raspberry Pi Zero   │
                         │       2 W           │
                         └──────────┬──────────┘
                                    │
             ┌──────────────────────┼─────────────────────┐
             │                      │                     │
             ▼                      ▼                     ▼
           Wi-Fi                   I²C                  UART
             │                      │                     │
             ▼                 ┌────┴────┐                ▼
        SSH / Connect          LCD     ADS1115         SIM800L


                         USB OTG / Gadget
                                │
                                ▼
                         Windows Laptop
                         USB Ethernet + SSH
```

### Primary interfaces

| Hardware               | Interface  | Purpose                      |
| ---------------------- | ---------- | ---------------------------- |
| LCD2004 + I²C backpack | I²C        | Display                      |
| ADS1115                | I²C        | Analog/current measurement   |
| SIM800L                | UART       | GSM/SMS communication        |
| Relay module           | GPIO       | Pump control                 |
| USB OTG                | USB Gadget | Emergency network/SSH access |
| Wi-Fi                  | WLAN       | Normal network/SSH access    |

---

# Hardware Requirements

Required:

* Raspberry Pi Zero 2 W
* MicroSD card — **16 GB minimum, 32 GB recommended**
* Suitable 5V power supply
* Micro-USB data cable (Optional)
* Wi-Fi hotspot/network


### Important USB cable requirement

For USB Gadget functionality, the cable must support **data transfer**.

A charging-only Micro-USB cable will power the Pi but will not create the USB network connection.

---

# Prerequisites

Before starting:

* [ ] Raspberry Pi Zero 2 W available
* [ ] SD card available
* [ ] USB data cable available (Optional)
* [ ] Wi-Fi credentials available
* [ ] Raspberry Pi Imager installed on laptop

---

# Raspberry Pi Imager

Download Raspberry Pi Imager from the official website:

**https://www.raspberrypi.com/software/**

## Select Device

Choose:

```text
Raspberry Pi Zero 2 W
```

## Select Operating System

Recommended:

```text
Raspberry Pi OS Lite (64-bit)
```

Reason:

* Headless system
* Lower memory usage
* No desktop environment
* Suitable for production
* Lower resource consumption


## Select Storage

Select the MicroSD card.

### WARNING

Make absolutely sure the selected device is the SD card.

Do **not** select your laptop's SSD.

---

# Imager OS Customisation


Configure the following.

## General

### Hostname

```text
swap-pi
```

## Localisation

Timezone:

```text
Asia/Kolkata
```

Keyboard layout:

```text
us
```

or your preferred layout.

---

### Username

Use the project user.

Example:

```text
pizero
```

### Password

Set a strong password.(This need to be enter while connecting to Pi)

---

## Wi-Fi

Configure:

```text
SSID: <YOUR_WIFI_NAME>
Password: <YOUR_WIFI_PASSWORD>
```

Use:

```text
India
```

for the WLAN country.

---



## Remote acess (SSH)

Enable:

```text
Enable SSH
```

Authentication:

```text
Use password authentication
```

SSH is required for remote administration(Headless mode).

---

## Raspberry Pi Connect

Enable:

```text
Enable Raspberry Pi Connect
```

This provides an additional remote-access mechanism.

It is **not a replacement for SSH**.

We maintain multiple access paths:

```text
Wi-Fi → SSH
Wi-Fi → Raspberry Pi Connect
USB → SSH
```

---

## Write SD Card

Review the settings.

Then:

```text
Next
→ Confirm
→ Write
```

Wait for:

```text
Writing: 100%
Verifying: 100%
```

Only remove the SD card after verification completes successfully.

---

# First Boot

Insert the SD card into the Raspberry Pi Zero 2 W.

Power the Pi.

Wait approximately:

```text
2–3 minutes
```

for the first boot.

---

# Find Raspberry Pi

From Windows:

```powershell
ping swap-pi.local
```

If hostname resolution does not work:

```powershell
arp -a
```

Alternatively, check the Wi-Fi router/hotspot DHCP client list.

---

# SSH Login

Use:

```powershell
ssh pizero@swap-pi.local
```

or:

```powershell
ssh pizero@<PI_IP_ADDRESS>
```

Example:

```powershell
ssh pizero@192.168.1.100
```

Verify hostname:

```bash
hostname
```

Expected:

```text
swap-pi
```

---

# Verify Operating System

Run:

```bash
cat /etc/os-release
```

Expected:

```text
Debian GNU/Linux 13 (trixie)
```

Also:

```bash
uname -a
```

---

# Basic System Configuration

Update the operating system:

```bash
sudo apt update
sudo apt upgrade -y
```

Reboot:

```bash
sudo reboot
```

Reconnect using SSH.

---

# Raspberry Pi Configuration Tool

Run:

```bash
sudo raspi-config
```

---

## Interface Options

### SSH

Enable:

```text
SSH → Enable
```

---

### I²C

Enable:

```text
I2C → Enable
```

Required for:

```text
LCD2004
ADS1115
```

---

### Serial Port

SIM800L communicates through UART.

Configure:

```text
Login shell over serial?
NO
```

```text
Enable serial port hardware?
YES
```

Final configuration:

```text
Serial login shell: DISABLED
UART hardware:       ENABLED
```

### Why?

The Linux serial login shell can interfere with the SIM800L communication.

---

## VNC

Optional (We can see Desktop of PI)

Recommended:

```text
Enable
```

---

## SPI

Not required for the current LCD/ADS1115/SIM800L setup.

Keep:

```text
Disabled
```

unless future hardware requires SPI.

---

## Camera

Not required.

Keep:

```text
Disabled
```

---

## Reboot

After configuration:

```bash
sudo reboot
```

---

# Raspberry Pi Connect

If Raspberry Pi Connect was not enabled during Imager setup, install it:

```bash
sudo apt update
sudo apt install rpi-connect -y
```

Sign in:

```bash
rpi-connect signin
```

Verify the device from:

**https://connect.raspberrypi.com/**

### Important

Raspberry Pi Connect requires network connectivity.

Therefore it should be treated as an **additional access method**, not the only recovery mechanism.

---

# USB Gadget — Emergency Network Access

## Purpose

USB Gadget provides a direct network connection between:

```text
Windows Laptop
       │
       │ USB
       ▼
Raspberry Pi Zero 2 W
```

This is particularly important if Wi-Fi stops working.

Normal access:

```text
Laptop
  │
 Wi-Fi
  │
  ▼
Pi
```

Emergency access:

```text
Laptop
  │
 USB
  │
  ▼
Pi
```

---

## Raspberry Pi OS Version

This guide uses the modern USB Gadget mechanism available on current Raspberry Pi OS Trixie.

Verify:

```bash
cat /etc/os-release
```

Confirm:

```text
VERSION_CODENAME=trixie
```

---

## Install USB Gadget Support

```bash
sudo apt update
sudo apt install rpi-usb-gadget -y
```

---

## Enable USB Gadget

```bash
sudo rpi-usb-gadget on
```

Reboot:

```bash
sudo reboot
```

---

## Verify USB Gadget

Run:

```bash
sudo rpi-usb-gadget status
```

Expected:

```text
USB Gadget mode is on
```

You should see:

```text
iface: usb0
```

---

## Verify USB Network Interface

```bash
ip addr show usb0
```

Example:

```text
usb0:
    inet 10.12.194.1/28
```

The exact address may vary.

Also:

```bash
ip link show usb0
```

### Before USB connection

You may see:

```text
NO-CARRIER
```

This means the Pi has configured the gadget but the USB physical connection has not been established.

After connecting a valid USB data cable, the interface should become:

```text
LOWER_UP
```

---

# USB Connection Hardware

### Important

On Raspberry Pi Zero 2 W, use the:

```text
USB DATA / OTG
```

micro-USB port.

Do not use:

```text
PWR IN
```

for USB Gadget data.

### Connection

```text
Raspberry Pi Zero 2 W
        │
        │ USB DATA/OTG
        ▼
Micro-USB data cable
        │
        ▼
Windows Laptop
```

The cable must support USB data.

---

# Windows USB Verification

After connecting the Pi to Windows:

```powershell
Get-NetAdapter
```

A new network adapter should appear.

Possible names include:

```text
USB Ethernet
USB Ethernet/RNDIS Gadget
Remote NDIS Compatible Device
Ethernet 2
```

The exact name depends on Windows.

Also:

```powershell
ipconfig
```

---

# USB SSH Recovery

Once the USB network connection is established, identify the Pi's USB IP:

```bash
ip addr show usb0
```

Example:

```text
10.12.194.1
```

From Windows:

```powershell
ssh pi@10.12.194.1
```

If the address differs, use the address displayed by:

```bash
ip addr show usb0
```

---

# USB Gadget Troubleshooting

If:

```text
usb0 exists
```

but:

```text
NO-CARRIER
```

check:

1. Correct USB port
2. Data-capable USB cable
3. Windows USB detection
4. Windows Device Manager
5. USB network adapter

Check Pi:

```bash
sudo rpi-usb-gadget status
```

Check:

```bash
ip link show usb0
```

Check USB controller:

```bash
ls -l /sys/class/udc/
```

### Important

Do not immediately modify the USB gadget configuration if `usb0` exists.

First check:

```text
Cable → Port → Windows detection → Pi link state
```

---

# Network Verification

## Wi-Fi

Check:

```bash
ip addr
```

Look for:

```text
wlan0
```

Check connectivity:

```bash
ping -c 4 google.com
```

Check DNS:

```bash
getent hosts google.com
```

---

## SSH

Check:

```bash
sudo systemctl status ssh
```

Expected:

```text
Active: active (running)
```

---

## Wi-Fi Failure Recovery Test

After USB Gadget has been successfully tested:

1. Connect Pi to laptop through USB.
2. Confirm USB SSH works.
3. Disconnect/disable Wi-Fi.
4. SSH through USB.

The objective is:

```text
Wi-Fi OFF
    ↓
USB SSH still works
    ↓
Diagnose Wi-Fi
```

This test should be performed **before deploying the final system**.

---

