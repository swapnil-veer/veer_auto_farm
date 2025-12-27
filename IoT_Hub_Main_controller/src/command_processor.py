import time
import threading

class CommandProcessor:
    """
    Processes relay commands one at a time sequentially using a list of dicts.
    Uses context manager for safe relay operations.
    Runs a continuous polling loop.
    """
    def __init__(self,pump_context_manager, phase_data, logger,poll_interval=5, event_handler=None):
        self.pump_context_manager = pump_context_manager
        self.phase_data = phase_data
        self.command_queue = []  # List of dicts: [{'mode': 'manual', 'duration_sec': 300, 'remaining_sec': 300, 'in_progress': False, 'start_time': None}, ...]
        self.current_command = None  # Currently processing dict
        self.poll_interval = poll_interval
        self.is_running = False
        self.is_auto_running = False  # Track AUTO mode state
        self.manual_stop = False
        self._lock = threading.Lock()
        self.logger = logger
        self.event_handler = event_handler  # callable or None

    def add_command(self,duration_minutes = None, mode = "manual", sender = None):
        """Add a new one-time command to the queue as a dict."""
        command_dict = {
            'mode' : mode,
            'duration_sec': duration_minutes * 60,
            'remaining_sec': duration_minutes * 60,
            'in_progress': False,
            'start_time': None,
            'sender': sender
        }
        self.command_queue.append(command_dict)
        self.logger.info(f"Command added: {command_dict}")
 
    def delete_one(self):
        if self.current_command:
            self.manual_stop = True
    
    def delete_all(self):
        self.delete_one()
        self.command_queue.clear()
        return True

    def reset_manual_stop(self):
        self.manual_stop = False
        
     # public entry point for main_controller
    def handle(self, command:dict):
        """Public entry point - MainController calls this"""
        ctype = command['ctype']
        self.logger.info(f"Handling command: {ctype} from {command['sender']}")
        
        if ctype == 'MANUAL_ON' or ctype == 'AUTO_ON':
            self._add_to_queue(command)
        elif ctype == 'DELETE_ONE':
            self.delete_one()
        elif ctype == 'DELETE_ALL':
            self.delete_all()
        else:
            self.logger.warning(f"Unknown ctype: {ctype}") 
            raise ValueError(f"Unknown command type: {ctype}") 

    def _is_auto_running(self) -> bool:
        """Check if currently processing AUTO command"""
        return (self.current_command and 
                self.current_command.get('mode') == 'auto' and 
                self.current_command.get('in_progress', False))    

    def _add_to_queue(self, command: dict):
        """Helper: MANUAL_ON → existing queue format"""
        if command['ctype'] == 'MANUAL_ON' and self._is_auto_running():
            # this will raise error if auto is running and we added manual command 
            raise ValueError("AUTO mode active. OFF first.")
        
        if command['ctype'] == 'MANUAL_ON':
            mode = 'manual'
            duration_sec = command.get('duration_sec')
            remaining_sec = command.get('remaining_sec')
        elif command['ctype'] == 'AUTO_ON':
            mode = 'auto'
            duration_sec = None
            remaining_sec = None  # explicit None for auto

        cmd_dict = {
            'mode': mode,  
            'duration_sec': duration_sec ,
            'remaining_sec': remaining_sec ,
            'in_progress': False,
            'start_time': None,
            'sender': command['sender']
        }

        self.command_queue.append(cmd_dict)
        self.logger.info(f"{command['ctype']} queued: {cmd_dict}")
      
    def _process_current_command(self, auto : bool):
        """Process the current command if power is available."""
        # if not self.current_command or self.current_command['remaining_sec'] <= 0:
        if not self.current_command :
            return
        self.logger.info(f"Starting processing : {self.current_command}")

        if self.phase_data['green_led'] == 1:
            with self.pump_context_manager:
                start_time = time.time()
                self.current_command['in_progress'] = True
                self.current_command['start_time'] = start_time

                self.logger.info(f"Pump ON: mode={self.current_command.get('mode')} sender={self.current_command.get('sender')}")

                # --- PUMP_STARTED event ---
                if self.event_handler and self.current_command:
                    cmd = self.current_command
                    event = {
                        "type": "PUMP_STARTED",
                        "timestamp": time.time(),  # datetime.now().isoformat()
                        "data": {
                            "sender": cmd.get("sender"),
                            "mode": cmd.get("mode"),
                            "duration_min": (
                                round(cmd["remaining_sec"] / 60)
                                if cmd.get("mode") == "manual" else None
                            ),
                        },
                    }
                    self.event_handler(event)
                # --- /PUMP_STARTED event ---
                
                while True:
                    if not auto:
                        if self.current_command['remaining_sec'] <= 0:
                            break
                        sleep_time = min(self.poll_interval, self.current_command['remaining_sec'])
                    else:
                        sleep_time = self.poll_interval
                    time.sleep((sleep_time))

                    if not auto:
                        # rewrite current command with remaining sec 
                        elapsed = time.time() - start_time
                        self.current_command['remaining_sec'] = max(0, self.current_command['remaining_sec'] - elapsed)
                        start_time = time.time()  # Reset start time for next iteration

                
                    if self.phase_data['green_led'] != 1:                   
                        # Power loss: rewrite command with remaining time
                        self.current_command['in_progress'] = False
                        if self.event_handler and self.current_command:
                            cmd = self.current_command
                            event = {
                            "type": "PUMP_ABORTED_POWER_LOSS",
                            "timestamp": time.time(),  # datetime.now().isoformat()
                            "data": {
                                "sender": cmd.get("sender"),
                                "mode": cmd.get("mode"),
                                "duration_min": (round(cmd["remaining_sec"] / 60) if cmd.get("mode") == "manual" else None
                                        ),
                                    },
                                }
                            self.event_handler(event)
                        self.logger.info("Power loss detected, command paused with remaining time.")

                        return  # Exit context and wait for next poll
                    
                    if self.manual_stop == True:
                        sender = self.current_command.get('sender')
                        copy_cmd = dict(self.current_command)

                        if self.event_handler and self.current_command:      
                            cmd = self.current_command
                            event = {
                                "type": "PUMP_AUTO_STOPPED" if auto else "PUMP_ABORTED_MANUAL_STOP",
                                "timestamp": time.time(),
                                "data": {
                                    "sender": cmd.get("sender"),
                                    "mode": cmd.get("mode"),
                                    "duration_min": round(cmd["remaining_sec"] / 60) if cmd.get("mode") == "manual" else None,
                                },
                            }
                            self.event_handler(event)
                        
                        self.current_command = None                       
                        self.reset_manual_stop()
                        return

                # Update remaining based on actual elapsed
                self.current_command['in_progress'] = False


        elif self.manual_stop == True:
            if self.event_handler and self.current_command:
                cmd = self.current_command
                event = {
                    "type": "COMMAND_DELETED_CURRENT",
                    "timestamp": time.time(),
                    "data": {
                        "sender": cmd.get("sender"),
                        "mode": cmd.get("mode"),
                        "duration_min": round(cmd["remaining_sec"] / 60) if cmd.get("mode") == "manual" else None,
                    },
                }
                self.event_handler(event)
            self.current_command = None
            self.reset_manual_stop()
            return
        else:
            self.logger.info("Waiting for power to process command.")

    def run(self):
        """Main continuous polling loop to process commands sequentially."""
        self.is_running = True
        self.logger.info("CommandProcessor started. Running continuously...")
        while self.is_running:
            # Dequeue next command if current is done and queue has items
            if self.current_command and self.current_command['mode'] != 'auto':
                if self.current_command['remaining_sec'] <= 0:
                    event = {
                            "type": "PUMP_COMPLETED",
                            "timestamp": time.time(),  # datetime.now().isoformat()
                            "data": {
                                "sender": self.current_command.get("sender"),
                                "mode": self.current_command.get("mode"),
                                "actual_min":  (
                                    round(self.current_command["duration_sec"] / 60)),
                                "duration_min": (
                                    round(self.current_command["duration_sec"] / 60)
                                    if self.current_command.get("mode") == "manual" else None
                                ),
                            },
                            }
                    if self.event_handler:
                        self.event_handler(event)
                    self.logger.info(f"Command segment completed. Remaining: {self.current_command['remaining_sec']} seconds.")
                    self.current_command = None

            time.sleep(5)   # time for delete all execute if abailable
            with self._lock:
                if not self.current_command and self.command_queue:
                    self.current_command = self.command_queue.pop(0)
                    # self._print_command(self.current_command, "Dequeued and set as current")

            # Process current if exists
            if self.current_command:
                if self.current_command['mode'] == 'auto':
                    self._process_current_command(auto=True)
                else:
                    self._process_current_command(auto=False)

            time.sleep(self.poll_interval)

        print("CommandProcessor stopped.")

    def stop(self):
        """Stop the processor."""
        self.is_running = False



