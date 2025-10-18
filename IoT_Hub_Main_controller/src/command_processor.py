import time
from modules.pump_control import pump_context_manager, pump_manager
from modules.phase_monitor import phase_data
from logging_config import logger
from modules.sim800l.sim import sms_thread
import threading




class CommandProcessor:
    """
    Processes relay commands one at a time sequentially using a list of dicts.
    Uses context manager for safe relay operations.
    Runs a continuous polling loop.
    """
    def __init__(self, pump_manager, poll_interval=5):
        self.pump_manager = pump_manager
        self.command_queue = []  # List of dicts: [{'duration_sec': 300, 'remaining_sec': 300, 'in_progress': False, 'start_time': None}, ...]
        self.current_command = None  # Currently processing dict
        self.poll_interval = poll_interval
        self.is_running = False
        self.manual_stop = False
        self._lock = threading.Lock()

    def add_command(self, duration_minutes, sender = None):
        """Add a new one-time command to the queue as a dict."""
        command_dict = {
            'duration_sec': duration_minutes * 60,
            'remaining_sec': duration_minutes * 60,
            'in_progress': False,
            'start_time': None,
            'sender': sender
        }
        self.command_queue.append(command_dict)
        if sender:
            sms_thread.send_sms(sender, f"Added {round(command_dict['remaining_sec']/60)} min command")  # Feedback
        logger.info(f"Command added: {command_dict}")

    def _print_command(self, command_dict, phase):
        """Helper to print command at a specific phase."""
        print(f"{phase}: {command_dict}")
    
    def delete_one(self):
        if self.current_command:
            self.manual_stop = True
            
    def delete_all(self):
        self.delete_one()
        self.command_queue.clear()
        return True

    def reset_manual_stop(self):
        self.manual_stop = False

    def _process_current_command(self):
        """Process the current command if power is available."""
        if not self.current_command or self.current_command['remaining_sec'] <= 0:
            return
        logger.info(f"Starting processing : {self.current_command}")

        if phase_data['green_led'] == 1:
            with pump_context_manager:
                start_time = time.time()
                self.current_command['in_progress'] = True
                self.current_command['start_time'] = start_time
                msg = f"Pump ON for {round(self.current_command['remaining_sec']/60)} min"
                sms_thread.send_sms(self.current_command.get('sender'), msg)  # Feedback
                
                while self.current_command['remaining_sec'] > 0:
                    sleep_time = min(self.poll_interval, self.current_command['remaining_sec'])
                    time.sleep(sleep_time)

                    # rewrite current command with remaining sec 
                    elapsed = time.time() - start_time
                    self.current_command['remaining_sec'] = max(0, self.current_command['remaining_sec'] - elapsed)
                    start_time = time.time()  # Reset start time for next iteration

 
                    if self.current_command['remaining_sec'] <= 0:
                        break

                    if phase_data['green_led'] != 1:
                        # Power loss: rewrite command with remaining time

                        self.current_command['in_progress'] = False
                        # self._print_command(self.current_command, "Power loss - updated")
                        logger.info(f"Power loss detected. Rewriting command with {self.current_command['remaining_sec']} seconds remaining.")
                        msg = f"Power loss. Waiting, {round(self.current_command['remaining_sec']/60)} min left"
                        sms_thread.send_sms(self.current_command.get('sender'), msg)  # Feedback
                        return  # Exit context and wait for next poll
                    
                    if self.manual_stop == True:
                        sender = self.current_command.get('sender')
                        copy_cmd = dict(self.current_command)
                        self.current_command = None
                        msg = f"Following command deleted {copy_cmd}"
                        sms_thread.send_sms(sender, msg)
                        self.reset_manual_stop()
                        return

                # Update remaining based on actual elapsed
                self.current_command['in_progress'] = False
                logger.info(f"Command segment completed. Remaining: {self.current_command['remaining_sec']} seconds.")
                msg = f"Pump completed. {round(self.current_command['duration_sec']/60)} min total"
                sms_thread.send_sms(self.current_command.get('sender'), msg)  # Feedback

        elif self.manual_stop == True:
            sender = self.current_command.get('sender')
            copy_cmd = dict(self.current_command)
            self.current_command = None
            msg = f"Following command deleted {copy_cmd}"
            sms_thread.send_sms(sender, msg)
            self.reset_manual_stop()
            return
        else:
            logger.info("Waiting for power to process command.")

    def run(self):
        """Main continuous polling loop to process commands sequentially."""
        self.is_running = True
        logger.info("CommandProcessor started. Running continuously...")
        while self.is_running:
            # Dequeue next command if current is done and queue has items
            if self.current_command and self.current_command['remaining_sec'] <= 0:
                original_duration = self.current_command['duration_sec']
                logger.info(f"Command fully completed: {round(original_duration / 60)} minutes total.")
                self.current_command = None

            time.sleep(5)   # time for delete all execute if abailable
            with self._lock:
                if not self.current_command and self.command_queue:
                    self.current_command = self.command_queue.pop(0)
                    # self._print_command(self.current_command, "Dequeued and set as current")

            # Process current if exists
            if self.current_command:
                self._process_current_command()

            time.sleep(self.poll_interval)

        print("CommandProcessor stopped.")

    def stop(self):
        """Stop the processor."""
        self.is_running = False

processor = CommandProcessor(pump_manager)
processor_thread = processor.run

# # Example usage
# if __name__ == "__main__":
#     pump_manager = RelayManager()
#     processor = CommandProcessor(pump_manager)

#     # Start the processor in a background thread (non-daemon to keep alive)
#     thread = threading.Thread(target=processor.run)
#     thread.start()

#     # Simulate adding commands and power changes (for demo; remove or comment in production)
#     time.sleep(1)
#     processor.add_command(30)  # Add 30 min command

#     # Simulate power
#     pump_manager.set_power(True)
#     time.sleep(10)  # Run for 10 sec
#     pump_manager.set_power(False)  # Power loss, should pause and rewrite
#     time.sleep(2)
#     pump_manager.set_power(True)  # Power back, continue
#     time.sleep(10)

#     # Add another command while processing
#     processor.add_command(5)  # Will queue and process after first completes

#     # Wait indefinitely until KeyboardInterrupt (Ctrl+C)
#     try:
#         thread.join()
#     except KeyboardInterrupt:
#         print("\nReceived KeyboardInterrupt. Stopping...")
#         processor.stop()
#         thread.join()