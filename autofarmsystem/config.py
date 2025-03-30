GPIO_PINS = {
    "sda" : 2, # I2C SDA (BCM 2, Pin 3)
    "scl" : 3,  #I2C SCL (BCM 3, Pin 5)
    "relay_pi_onoff" : 23,  #(Pi On-Off Relay) (BCM 23, Pin 16)
    "relay_dry_run" : 24,   #(Dry-Run Control Relay) (BCM 24, Pin 18)
    "phase_monitor_green" : 17, # Phase Monitor - OK (Green LED) (BCM 17, Pin 11)
    "phase_monitor_yellow" : 27,    # Phase Monitor - Initial Wait (Yellow LED) (BCM 27, Pin 13)
    "phase_monitor_red" : 22,       # Phase Monitor - Fault (Red LED) (BCM 22, Pin 15)
    "bypass_switch" :11,            # DPST Switch 2A (BCM 11, Pin 23)
}

