# 🚀 Managing systemd Services (Raspberry Pi / Linux)

This document explains **how to create, enable, disable, debug, and remove a systemd service** for running a Python project automatically on boot.
Useful for **IoT, Raspberry Pi, server-side, and production-grade applications**.

---

## 📌 What is a systemd service?

A **systemd service** is a background process managed by Linux that:

* Can start automatically on boot
* Can be manually started/stopped
* Can restart automatically on failure
* Is widely used in production systems

---

## 📂 Service File Location

Custom services are stored at:

```bash
/etc/systemd/system/
```

Example:

```bash
veer-auto-farm.service
```

---

## 🚀 How to CREATE a systemd Service

### 1️⃣ Create the service file

```bash
sudo nano /etc/systemd/system/veer-auto-farm.service
```

### Paste the following content:

```ini
[Unit]
Description=Veer Auto Farm Controller
After=network.target

[Service]
User=pizero
WorkingDirectory=/home/pizero/projects/veer_auto_farm/IoT_Hub_Main_controller/src
ExecStart=/home/pizero/projects/veer_auto_farm/venv1/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save and exit:

* `CTRL + O` → Enter
* `CTRL + X`

---

### 2️⃣ Reload systemd (MANDATORY)

```bash
sudo systemctl daemon-reload
```

---

### 3️⃣ Enable service (auto-run on boot)

```bash
sudo systemctl enable veer-auto-farm.service
```

---

### 4️⃣ Start service immediately

```bash
sudo systemctl start veer-auto-farm.service
```

---

## ⛔ How to DISABLE Auto-Run

### Stop service now

```bash
sudo systemctl stop veer-auto-farm.service
```

### Disable service from starting on boot

```bash
sudo systemctl disable veer-auto-farm.service
```

---

## 🧪 How to CHECK Status & Debug
### Check list of services running

```bash
ls /etc/systemd/system/
```
### Check service status

```bash
sudo systemctl status veer-auto-farm.service
```

---

### View logs

```bash
journalctl -u veer-auto-farm.service
```

---

### View live logs (real-time)

```bash
journalctl -u veer-auto-farm.service -f
```

---

## 🗑️ How to REMOVE Service Completely

```bash
sudo rm /etc/systemd/system/veer-auto-farm.service
sudo systemctl daemon-reload
```

---

## ✅ Best Practices

* Use **systemd** instead of `cron` or `.bashrc`
* Always use **full paths** in `ExecStart`
* Use **virtual environment python**
* Keep service **disabled during development**
* Enable only in **production / deployment mode**

---

## 🎯 Interview-Ready Summary

> “I use systemd services to manage long-running applications.
> I define a service file under `/etc/systemd/system/`, specify execution details, and control auto-start using `systemctl enable` or `disable`.
> This approach provides reliability, restart handling, and production-level control.”

---

📌 **End of Document**
