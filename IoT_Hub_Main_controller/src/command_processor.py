import time
import threading
from logging_config import logger
from database.models.command import Command, CommandStatus, CommandType
from datetime import datetime

class CommandProcessor:
    """
    Processes relay commands one at a time sequentially using a list of dicts.
    Uses context manager for safe relay operations.
    Runs a continuous polling loop.
    """
    def __init__(self,pump_context_manager,poll_interval=5, event_handler=None, power_service = None):
        self.pump_context_manager = pump_context_manager
        self.command_queue = []  # List of dicts: [{'mode': 'manual', 'duration_sec': 300, 'remaining_sec': 300, 'in_progress': False, 'start_time': None}, ...]
        self.current_command = None  # Currently processing dict
        self.poll_interval = poll_interval
        self.is_running = False
        self.is_auto_running = False  # Track AUTO mode state
        self.manual_stop = False
        self._lock = threading.Lock()
        self.logger = logger
        self.event_handler = event_handler  # callable or None
        self.power_service = power_service
 
    def delete_one(self):
        if self.current_command:
            self.manual_stop = True
    
    def delete_all(self):
        self.delete_one()
        self.command_queue.clear()
        return True

    def reset_manual_stop(self):
        self.manual_stop = False

    def stop(self):
        """Stop the processor."""
        self.is_running = False
      
    def get_command(self, command_id: int) -> dict:
        """Fetch a Command by ID and return it as a dict."""
        db_cmd = self.db_session.query(Command).get(command_id)
        if not db_cmd:
            return {}
        return db_cmd

    def _create_command(self, ctype: str, sender: str, duration_minutes: int = None, sms_log_id: int = None, user_id: int = None) -> dict:
        """Factory: SMS intent → standard command_dict
            Creating commands for command processor     """
        priority_map = {
            'MANUAL_ON': 1,
            'AUTO_ON': 2,
            'DELETE_ONE': 3,
            'DELETE_ALL': 4
        }

        # DB CREATE (NEW)
        db_cmd = Command(
            ctype=ctype,
            priority=priority_map[ctype],
            sender_phone=sender,
            sms_log_id=sms_log_id,     # Optional FK
            user_id=user_id,           # Optional FK
            status=CommandStatus.CREATED,
            duration_sec=None,
            remaining_sec=duration_minutes * 60 if duration_minutes else None
        )
        self.db_session.add(db_cmd)
        self.db_session.commit()
        return db_cmd
        
    
     # public entry point for main_controller
    def handle(self, ctype: str, sender: str, duration_minutes: int = None, sms_log_id: int = None, user_id: int = None):
        """Public entry point - MainController calls this"""
        db_cmd = self._create_command(ctype=ctype,sender = sender, duration_minutes = duration_minutes, sms_log_id=sms_log_id, user_id = user_id)

        self.logger.info(f"Handling command: {db_cmd.id} from {user_id}")

        if ctype == CommandType.MANUAL_ON or ctype == CommandType.AUTO_ON:
            db_cmd.status = CommandStatus.QUEUED 
            self._emit_event(event_type="COMMAND_QUEUED", details={  # #command added to queue msg to user!
                    "command_id": db_cmd.id,
                    "ctype": db_cmd.ctype.value,
                    "duration_min": db_cmd.duration_sec // 60 if db_cmd.duration_sec else None,
                    "sender": db_cmd.sender_phone,
                    "position": self._get_queue_position(db_cmd.id)  # Bonus: queue position
                })  
        elif ctype == CommandType.DELETE_ONE:
            db_cmd.status = CommandStatus.COMPLETED
            self._delete_one()           
        elif ctype == CommandType.DELETE_ALL:
            db_cmd.status = CommandStatus.COMPLETED
            self._delete_all()           
        else:
            self.logger.warning(f"Unknown ctype: {ctype}") 
            raise ValueError(f"Unknown command type: {ctype}") 
        self.db_session.commit()


    def run(self):
        """Main loop: Resume ABORTED → Process QUEUED"""
        self.is_running = True
        self.logger.info("CommandProcessor started. Running continuously...")
        
        while self.is_running:
            # 1. RESUME ABORTED (power loss recovery)
            aborted_cmd = self.db_session.query(Command).filter(
                Command.status == CommandStatus.ABORTED
            ).order_by(Command.priority, Command.created_at).first()
            
            if aborted_cmd:
                self.logger.info(f"Resuming ABORTED command #{aborted_cmd.id}")
                self._process_db_command(aborted_cmd)
                continue
            
            # 2. NEW COMMANDS
            queued_cmd = self.db_session.query(Command).filter(
                Command.status == CommandStatus.QUEUED
            ).order_by(Command.priority, Command.created_at).first()
            
            if queued_cmd:
                self._process_db_command(queued_cmd)
            
            time.sleep(self.poll_interval)


    def _process_db_command(self,db_cmd: Command):
        """Full DB lifecycle: QUEUED → RUNNING → COMPLETED/ABORTED"""
        
        # 2. FAST CACHE for pump loop
        self.current_command = db_cmd

        is_auto = db_cmd.ctype == CommandType.AUTO_ON
        
        try:
            # 4. PUMP EXECUTION (your existing logic → DB-ready)
            if self.power_service.is_power_available():
                with self.pump_context_manager:
                    start_time = time.time()
                    db_cmd.status = CommandStatus.RUNNING
                    db_cmd.in_progress = True
                    db_cmd.start_time = datetime.utcnow()
                    self.db_session.commit()
                    
                    self._emit_event("PUMP_STARTED", db_cmd)  # Event first!
                    self.logger.info(f"Pump ON: Command #{db_cmd.id}, mode= {db_cmd.mode}")
                    
                    while True:
                        # CHECK EXIT CONDITIONS
                        if self._should_exit_pump(db_cmd): #if time complete in manual mode then break
                            break
                            
                        # POWER CHECK
                        if not self.power_service.is_power_available():
                            self._handle_power_loss(db_cmd)
                            return
                        
                        # MANUAL STOP CHECK  
                        if self.manual_stop:
                            self._handle_manual_stop(db_cmd)
                            return

                        # TIMER
                        elapsed = time.time() - start_time
                        start_time = time.time()            # start time reset                     

                        if not is_auto:
                            # UPDATE DB remaining_sec
                            db_cmd.remaining_sec = max(0, db_cmd.remaining_sec - elapsed)

                        db_cmd.duration_sec += elapsed      #this for auto and manual
                        self.db_session.commit()

                        time.sleep(self.poll_interval)
            
            # 5. SUCCESS COMPLETION
            self._complete_command_success(db_cmd)
            
        except Exception as e:
            # 6. ERROR HANDLING
            self._complete_command_error(db_cmd, str(e))
        
        finally:
            self.current_command = None

    def _should_exit_pump(self, db_cmd:Command) -> bool:
        """Timer-only exit (manual_stop handled separately)"""
        is_auto = db_cmd.ctype == CommandType.AUTO_ON
        return (not is_auto and db_cmd.remaining_sec <= 0)
                
    def _handle_power_loss(self, db_cmd: Command):
        """Power loss - Consistent dict event"""
        self._update_db_command(db_cmd, status=CommandStatus.ABORTED, in_progress=False)
        self._emit_event("PUMP_ABORTED_POWER_LOSS", {
            "command_id": db_cmd.id,
            "remaining_min": round(db_cmd.remaining_sec / 60),  # ORM attribute
            "sender": db_cmd.sender_phone
        })

    def _handle_manual_stop(self, db_cmd: Command):
        """Manual stop - Consistent dict event"""
        self._update_db_command(db_cmd, status=CommandStatus.TERMINATED, in_progress=False)
        is_auto = db_cmd.ctype == CommandType.AUTO_ON
        event_type = "PUMP_AUTO_STOPPED" if is_auto else "PUMP_ABORTED_MANUAL_STOP"
        self._emit_event(event_type, {
            "command_id": db_cmd.id,
            "sender": db_cmd.sender_phone,
            "ctype": db_cmd.ctype.value  # 'MANUAL_ON'
        })
        self.reset_manual_stop()

    def _complete_command_success(self, db_cmd: Command):
        """Success - Consistent dict event"""
        self._update_db_command(db_cmd, 
                            status=CommandStatus.COMPLETED, 
                            in_progress=False,
                            completed_at=datetime.utcnow())
        self._emit_event("PUMP_COMPLETED", {
            "command_id": db_cmd.id,
            "sender": db_cmd.sender_phone,
            "total_runtime_min": round(db_cmd.duration_sec / 60)
        })

    def _complete_command_error(self, db_cmd: Command, error_msg: str):
        """Error completion state transition"""
        self._update_db_command(db_cmd, 
                            status=CommandStatus.FAILED,  # Or ABORTED
                            in_progress=False,
                            completed_at=datetime.utcnow())
        
        self.logger.error(f"Command #{db_cmd.id} failed: {error_msg}")
        
        self._emit_event("PUMP_ERROR", {
            "command_id": db_cmd.id,
            "error": error_msg[:100],  # Truncate for SMS
            "sender": db_cmd.sender_phone
        })

    def _emit_event(self, event_type: str, details: dict = None):
        """Unified event emission - dict OR ORM"""
        if self.event_handler:
            event_data = details
            if hasattr(details, 'id'):  # ORM object fallback
                event_data = {
                    "command_id": details.id,
                    "sender": details.sender_phone,
                    "ctype": details.ctype.value
                }
            
            event = {
                "type": event_type,
                "timestamp": time.time(),
                "data": event_data
            }
            self.event_handler(event)

    def _update_db_command(self, db_cmd : Command, **updates):
        """Atomic DB updates"""
        for key, value in updates.items():
            setattr(db_cmd, key, value)
        self.db_session.commit()

    def _delete_one(self, trigger_cmd: Command):
        """Kill CURRENT RUNNING pump only"""
        running_cmd = self.db_session.query(Command).filter(
            Command.status == CommandStatus.RUNNING,
            Command.in_progress == True
        ).first()
        
        if running_cmd:
            self.logger.info(f"DELETE_ONE: Stopping RUNNING #{running_cmd.id}")
            self.manual_stop = True  # Triggers _handle_manual_stop()
            return True
        return False

    def _delete_all(self, trigger_cmd: Command):
        """1st TERMINATE pending → 2nd _delete_one() running"""
        
        # 1. FIRST: TERMINATE ALL QUEUED/ABORTED
        pending_cmds = self.db_session.query(Command).filter(
            Command.status.in_([CommandStatus.QUEUED, CommandStatus.ABORTED])
        ).all()
        
        for cmd in pending_cmds:
            self._update_db_command(cmd, 
                                status=CommandStatus.TERMINATED,
                                terminated_by=trigger_cmd.id)
        
        deleted_count = len(pending_cmds)
        
        # 2. THEN: Reuse _delete_one() for RUNNING
        running_stopped = self._delete_one(trigger_cmd)
        
        self.logger.info(f"DELETE_ALL: TERMINATED {deleted_count} pending, "
                        f"running_stopped={running_stopped}")
        
        # 3. SINGLE EVENT - Complete status
        self._emit_event("PUMP_CLEARED_ALL", {
            "deleted_count": deleted_count,
            "running_stopped": running_stopped,
            "trigger_id": trigger_cmd.id,
            "sender": trigger_cmd.sender_phone
        })

    def _get_queue_position(self, cmd_id: int) -> int:
        """Position in QUEUED/ABORTED queue"""
        cmd = self.db_session.query(Command).get(cmd_id)
        if cmd.status not in [CommandStatus.QUEUED, CommandStatus.ABORTED]:
            return 0
        
        ahead_count = self.db_session.query(Command).filter(
            Command.status.in_([CommandStatus.QUEUED, CommandStatus.ABORTED]),
            Command.priority < cmd.priority,
            or_(Command.priority == cmd.priority, Command.created_at < cmd.created_at)
        ).count()
        return ahead_count + 1