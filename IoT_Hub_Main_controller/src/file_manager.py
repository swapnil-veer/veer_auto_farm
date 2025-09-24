import csv
import os
import threading
import settings


def sd_to_csv(filepath, sensor_dict):
    file_exists = os.path.isfile(filepath)

    with open(filepath, 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=sensor_dict.keys())

        # Write header only if file is new
        if not file_exists:
            writer.writeheader()

        writer.writerow(sensor_dict)


def log_sensors(sensors):
    threads = []

    for sensor_name in sensors.keys() :
        sensor_conf = sensors.get(sensor_name)

        # Skip if disabled or not defined
        if not sensor_conf or not sensor_conf["enabled"]:
            continue  

        filepath = os.path.join(settings.CSV_LOG_DIR, sensor_conf["file"])
        sensor_data = sensor_conf['data']

        t = threading.Thread(target=sd_to_csv, args=(filepath,sensor_data))
        t.start()
        threads.append(t)


if __name__ == "__main__":
    pass