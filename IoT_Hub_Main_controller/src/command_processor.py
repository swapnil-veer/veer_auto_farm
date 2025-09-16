import time
from modules.pump_control import pump_context_manager, pump_manager

processor = CommandProcessor(pump_manager)
processor_thread = processor.run

class CommandProcessor:
    """
    Processes relay commands one at a time sequentially using a list of dicts.
    Uses context manager for safe relay operations.
    Runs a continuous polling loop.
    """
    def __init__(self, pump_manager, poll_interval=1):
        self.pump_manager = pump_manager
        self.command_queue = []  # List of dicts: [{'duration_sec': 300, 'remaining_sec': 300, 'in_progress': False, 'start_time': None}, ...]
        self.current_command = None  # Currently processing dict
        self.poll_interval = poll_interval
        self.is_running = False

    def add_command(self, duration_minutes):
        """Add a new one-time command to the queue as a dict."""
        command_dict = {
            'duration_sec': duration_minutes ,
            'remaining_sec': duration_minutes,
            'in_progress': False,
            'start_time': None
        }
        self.command_queue.append(command_dict)
        print(f"Command added: {command_dict}")

    def _process_current_command(self):
        """Process the current command if power is available."""
        if not self.current_command or self.current_command['remaining_sec'] <= 0:
            return

        self._print_command(self.current_command, "Starting processing")

        if self.pump_manager.power:
            with pump_context_manager:
                start_time = time.time()
                self.current_command['in_progress'] = True
                self.current_command['start_time'] = start_time
                print(f"Processing command: {self.current_command['remaining_sec']} seconds remaining.")
                
                while self.current_command['remaining_sec'] > 0:
                    sleep_time = min(self.poll_interval, self.current_command['remaining_sec'])
                    time.sleep(sleep_time)

                    # rewrite current command with remaining sec 
                    elapsed = time.time() - start_time
                    self.current_command['remaining_sec'] = max(0, self.current_command['remaining_sec'] - elapsed)
                    start_time = time.time()  # Reset start time for next iteration

 
                    if self.current_command['remaining_sec'] <= 0:
                        break

                    if not self.pump_manager.power:
                        # Power loss: rewrite command with remaining time

                        self.current_command['in_progress'] = False
                        self._print_command(self.current_command, "Power loss - updated")
                        print(f"Power loss detected. Rewriting command with {self.current_command['remaining_sec']} seconds remaining.")
                        return  # Exit context and wait for next poll

                # Update remaining based on actual elapsed
                self.current_command['in_progress'] = False
                self._print_command(self.current_command, "Segment completed")
                print(f"Command segment completed. Remaining: {self.current_command['remaining_sec']} seconds.")
        else:
            print("Waiting for power to process command.")

    def run(self):
        """Main continuous polling loop to process commands sequentially."""
        self.is_running = True
        print("CommandProcessor started. Running continuously...")

        while self.is_running:
            # Dequeue next command if current is done and queue has items
            if self.current_command and self.current_command['remaining_sec'] <= 0:
                original_duration = self.current_command['duration_sec']
                print(f"Command fully completed: {original_duration / 60} minutes total.")
                self.current_command = None

            if not self.current_command and self.command_queue:
                self.current_command = self.command_queue.pop(0)
                self._print_command(self.current_command, "Dequeued and set as current")

            # Process current if exists
            if self.current_command:
                self._process_current_command()

            time.sleep(self.poll_interval)

        print("CommandProcessor stopped.")

    def stop(self):
        """Stop the processor."""
        self.is_running = False

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