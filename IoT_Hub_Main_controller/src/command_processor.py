import time
import threading
from logging_config import logger
from database.models.command import Command, CommandStatus, CommandType
from datetime import datetime
from app import db

class CommandProcessor:
    """
    Processes relay commands one at a time sequentially using a list of dicts.
    Uses context manager for safe relay operations.
    Runs a continuous polling loop.
    """
    def __init__(self,pump_context_manager,poll_interval=10, event_handler=None, power_service = None, app = None):
        self.pump_context_manager = pump_context_manager
        self.command_queue = []  # List of dicts: [{'mode': 'manual', 'duration_sec': 300, 'remaining_sec': 300, 'in_progress': False, 'start_time': None}, ...]
        self.cmd_id = None  # Currently processing dict
        self.poll_interval = poll_interval
        self.is_running = False
        self.is_auto_running = False  # Track AUTO mode state
        self.manual_stop = False
        self._lock = threading.Lock()
        self.logger = logger
        self.event_handler = event_handler  # callable or None
        self.power_service = power_service
        self.app = app
 
    def delete_one(self):
        if self.cmd_id:
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
      
    def get_command(self, command_id: int = None) -> dict:
        """Get Command by ID as dict (safe outside app context)."""
        if command_id == None:
            return {}
        with self.app.app_context():
            db_cmd = db.session.query(Command).get(command_id)
            if not db_cmd:
                return {}
            
            # ✅ Return serializable dict (no SQLAlchemy objects)
            return {
                'id': db_cmd.id,
                'ctype': db_cmd.ctype.name if db_cmd.ctype else None,
                'status': db_cmd.status.name if db_cmd.status else None,
                'mode': 'manual' if db_cmd.ctype == CommandType.MANUAL_ON else 'auto',
                'created_at': db_cmd.created_at.isoformat() if db_cmd.created_at else None,
                'duration_sec': getattr(db_cmd, 'duration_sec', 0),
                'remaining_sec': getattr(db_cmd, 'remaining_sec', 0),
            }


    def _create_command(self, ctype: CommandType, sender: str, duration_minutes: int = None, sms_log_id: int = None, user_id: int = None) -> dict:
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
            # ctype = CommandType.MANUAL_ON,
            priority=priority_map[ctype.value],
            sender_phone=sender,
            sms_id=sms_log_id,     # Optional FK
            user_id=user_id,           # Optional FK
            status = CommandStatus.CREATED,
            duration_sec=None,
            remaining_sec=duration_minutes * 60 if duration_minutes else None
        )
        
        db.session.add(db_cmd)
        db.session.commit()
        return db_cmd
            
     # public entry point for main_controller
    def handle(self, ctype: CommandType, sender: str, duration_minutes: int = None, sms_log_id: int = None, user_id: int = None):
        """Public entry point - MainController calls this"""
        with self.app.app_context():
            db_cmd = self._create_command(ctype=ctype,sender = sender, duration_minutes = duration_minutes, sms_log_id=sms_log_id, user_id = user_id)

            self.logger.info(f"Handling command: {db_cmd.id} from user {user_id}")

            if ctype == CommandType.MANUAL_ON or ctype == CommandType.AUTO_ON:
                db_cmd.status = CommandStatus.QUEUED 
                self._emit_event(event_type="COMMAND_QUEUED", details={  # #command added to queue msg to user!
                        "command_id": db_cmd.id,
                        "ctype": db_cmd.ctype.value,
                        "duration_min": db_cmd.remaining_sec // 60 if db_cmd.remaining_sec else None,
                        "sender": db_cmd.sender_phone,
                        "position": self._get_queue_position(db_cmd.id)  # Bonus: queue position
                    })  
                
            elif ctype == CommandType.DELETE_ONE:
                db_cmd.status = CommandStatus.COMPLETED
                self._delete_one(db_cmd.id)           
            elif ctype == CommandType.DELETE_ALL:
                db_cmd.status = CommandStatus.COMPLETED
                self._delete_all(db_cmd.id)           
            else:
                self.logger.warning(f"Unknown ctype: {ctype}") 
                raise ValueError(f"Unknown command type: {ctype}") 
            db.session.commit()


    def run1(self):
        """Main loop: Resume ABORTED → Process QUEUED"""
        self.is_running = True
        self.logger.info("CommandProcessor started. Running continuously...")
        
        while self.is_running:
            # 1. RESUME ABORTED (power loss recovery)
            with self.app.app_context():
                aborted_cmd = Command.query.filter_by(
                    status = CommandStatus.ABORTED
                ).order_by( Command.priority, Command.created_at).first()
            
                if aborted_cmd:
                    self.logger.info(f"Resuming ABORTED command #{aborted_cmd.id}")
                    self._process_db_command(aborted_cmd.id)
            
                else:
                    # 2. NEW COMMANDS
                    queued_cmd = Command.query.filter_by(
                        status = CommandStatus.QUEUED
                    ).order_by(Command.priority, Command.created_at).first()
            
                    if queued_cmd:
                        self._process_db_command(queued_cmd.id)
            
            time.sleep(self.poll_interval)
    def run(self):
        """Main loop: resume waiting/aborted work first, then process queued work."""
        self.is_running = True
        self.logger.info("CommandProcessor started. Running continuously...")

        while self.is_running:
            try:
                waiting_cmd = self.get_waiting_for_power_command()

                if waiting_cmd:
                    self.logger.info(
                        f"Resuming waiting command #{waiting_cmd.id} (status={waiting_cmd.status})"
                    )
                    self._process_db_command(waiting_cmd.id)

                else:
                    next_cmd = self.get_next_queued_command()

                    if next_cmd:
                        self.logger.info(f"Processing queued command #{next_cmd.id}")
                        self._process_db_command(next_cmd.id)

            except Exception as exc:
                self.logger.exception(f"CommandProcessor loop error: {exc}")

            time.sleep(self.poll_interval)


    def get_waiting_for_power_command(self):
        """
        Return the highest-priority command that is not completed because power is unavailable.
        For now ABORTED is treated as waiting-for-power recovery.
        """
        with self.app.app_context():
            return (
                Command.query
                .filter_by(status=CommandStatus.ABORTED)
                .order_by(Command.priority, Command.created_at)
                .first()
            )


    def get_next_queued_command(self):
        """Return the next queued command to be executed."""
        with self.app.app_context():
            return (
                Command.query
                .filter_by(status=CommandStatus.QUEUED)
                .order_by(Command.priority, Command.created_at)
                .first()
            )


    def get_queued_commands(self, limit=None):
        """Return queued commands ordered by priority and creation time."""
        with self.app.app_context():
            query = (
                Command.query
                .filter_by(status=CommandStatus.QUEUED)
                .order_by(Command.priority, Command.created_at)
            )
            rows = query.limit(limit).all() if limit else query.all()

            return [
                {
                    "id": cmd.id,
                    "mode": cmd.mode,
                    "status": cmd.status.name if hasattr(cmd.status, "name") else str(cmd.status),
                    "priority": cmd.priority,
                    "created_at": cmd.created_at.isoformat() if cmd.created_at else None,
                }
                for cmd in rows
            ]
    
    def _process_db_command(self,cmd_id: int):
        """Full DB lifecycle: QUEUED → RUNNING → COMPLETED/ABORTED"""
        # 2. FAST CACHE for pump loop   
        self.cmd_id = cmd_id

        with self.app.app_context():
            db_cmd = Command.query.get(cmd_id)
            is_auto = db_cmd.ctype == CommandType.AUTO_ON
            duration_sec = db_cmd.duration_sec or 0
        
        try:
            # 4. PUMP EXECUTION (your existing logic → DB-ready)
            if self.power_service.is_power_available():
                self.pump_context_manager.set_cmd_id(cmd_id)
                with self.pump_context_manager:
                    start_time = time.time()
                    with self.app.app_context():
                        db_cmd = Command.query.get(cmd_id)
                        db_cmd.status = CommandStatus.RUNNING
                        db_cmd.in_progress = True
                        db_cmd.start_time = datetime.utcnow()
                        db.session.commit()
                        details = {
                                    "command_id": db_cmd.id,
                                    "sender": db_cmd.sender_phone,
                                    "mode": "manual" if db_cmd.ctype == CommandType.MANUAL_ON else "auto",
                                    "duration_min": db_cmd.remaining_sec // 60 if db_cmd.remaining_sec else None,
                                }
                    
                    self._emit_event("PUMP_STARTED", details)
                    self.logger.info(f"Pump ON: Command #{details.get('command_id')}, mode= {details.get('mode')}")
                    
                    while True:
                        # CHECK EXIT CONDITIONS
                        if self._should_exit_pump(cmd_id): #if time complete in manual mode then break
                            break
                        # POWER CHECK
                        if not self.power_service.is_power_available():
                            self._handle_power_loss(cmd_id)
                            return
                        
                        # MANUAL STOP CHECK  
                        if self.manual_stop:
                            self._handle_manual_stop(cmd_id)
                            return

                        # TIMER                     
                        elapsed = time.time() - start_time
                        duration_sec += elapsed
                        start_time = time.time()
                        self._update_db_command(
                            cmd_id=db_cmd.id,
                            duration_sec= round(duration_sec,2),
                        )
                        time.sleep(self.poll_interval)
            
                    # 5. SUCCESS COMPLETION
                    self._complete_command_success(cmd_id)
            
        except Exception as e:
            # 6. ERROR HANDLING
            self._complete_command_error(cmd_id, str(e))
        
        finally:
            self.cmd_id = None

    def _should_exit_pump(self, cmd_id: int) -> bool:
        """Timer-only exit (manual_stop handled separately)"""
        with self.app.app_context():
            db_cmd = Command.query.get(cmd_id)
            
            if not db_cmd:
                return True
            
            is_auto = db_cmd.ctype == CommandType.AUTO_ON
            if not is_auto and db_cmd.remaining_sec is not None:
                return (db_cmd.duration_sec or 0) >= (db_cmd.remaining_sec or 0)
            return False

                
    def _handle_power_loss(self, cmd_id: int):
        """Power loss - Consistent dict event"""
        with self.app.app_context():
            db_cmd = Command.query.get(cmd_id)
            event = {                                           # for event emiting
            "command_id": db_cmd.id,
            "remaining_min": round(db_cmd.remaining_sec / 60),  # ORM attribute
            "sender": db_cmd.sender_phone
        }
        self._update_db_command(cmd_id, status=CommandStatus.ABORTED, in_progress=False)
        self._emit_event("PUMP_ABORTED_POWER_LOSS", event)

    def _handle_manual_stop(self, cmd_id: int):
        """Manual stop - Consistent dict event"""
        with self.app.app_context():
            db_cmd = Command.query.get(cmd_id)
            is_auto = db_cmd.ctype == CommandType.AUTO_ON
            event_type = "PUMP_AUTO_STOPPED" if is_auto else "PUMP_ABORTED_MANUAL_STOP"

            event = {                           # for event emiting
                "command_id": db_cmd.id,
                "sender": db_cmd.sender_phone,
                "ctype": db_cmd.ctype.value  # 'MANUAL_ON'
            }
        self._update_db_command(cmd_id, status=CommandStatus.TERMINATED, in_progress=False)
        self._emit_event(event_type, event)
        self.reset_manual_stop()

    def _complete_command_success(self, cmd_id: int):
        """Success - Consistent dict event"""
        with self.app.app_context():
            db_cmd = Command.query.get(cmd_id)

            event_data = {                      # for event emiting
            "command_id": db_cmd.id,
            "sender": db_cmd.sender_phone,
            "total_runtime_min": round(max(0, db_cmd.duration_sec) / 60)
        }
        self._update_db_command(cmd_id,  
                            status=CommandStatus.COMPLETED, 
                            in_progress=False,
                            completed_at=datetime.utcnow())
        self._emit_event("PUMP_COMPLETED", event_data)

    def _complete_command_error(self, cmd_id: int, error_msg: str):
        """Error completion state transition"""
        with self.app.app_context():
            db_cmd = Command.query.get(cmd_id)
            event_data = {                      # for event emiting
            "command_id": db_cmd.id,
            "error": error_msg[:100],  # Truncate for SMS
            "sender": db_cmd.sender_phone
        }
        self._update_db_command(cmd_id, 
                            status=CommandStatus.ABORTED,  # Or ABORTED
                            in_progress=False,
                            completed_at=datetime.utcnow()) 
        time.sleep(10)     
        self._emit_event("PUMP_ERROR", event_data)
        self.logger.error(f"Command #{db_cmd.id} failed: {error_msg}")


    def _emit_event(self, event_type: str, details: dict = None):
        """Unified event emission - dict OR ORM"""
        if self.event_handler:
            event_data = details
            if hasattr(details, 'id'):  # ORM object fallback
                event_data = {
                    "command_id": details.id,
                    "sender": details.sender,
                    "ctype": details.ctype.value
                }
            event = {
                "type": event_type,
                "timestamp": time.time(),
                "data": event_data
            }
            self.event_handler(event)

    def _update_db_command(self, cmd_id: int, **updates):
        """Atomic DB updates"""
        with self.app.app_context():
            Command.query.filter_by(id=cmd_id).update(updates) 
            db.session.commit()

    def _delete_one(self, cmd_id: int):
        """Kill CURRENT RUNNING pump only"""
        with self.app.app_context():
            running_cmd = Command.query.filter(
                Command.status == CommandStatus.RUNNING,
                Command.in_progress == True
            ).first()
            cmd_id = running_cmd.id
        
        if running_cmd:
            self.logger.info(f"DELETE_ONE: Stopping RUNNING #{cmd_id}")
            self.manual_stop = True  # Triggers _handle_manual_stop()
            return True
        return False

    def _delete_all(self, trigger_id: int):
        """1st TERMINATE pending → 2nd _delete_one() running"""
        # 1. FIRST: TERMINATE ALL QUEUED/ABORTED
        with self.app.app_context():
            pending_cmds = Command.query.filter(
                Command.status.in_([CommandStatus.QUEUED, CommandStatus.ABORTED])
            ).all()
        
        for cmd in pending_cmds:
            self._update_db_command(cmd.id, 
                                status=CommandStatus.TERMINATED,
                                terminated_by=trigger_id)
        
        deleted_count = len(pending_cmds)
        
        # 2. THEN: Reuse _delete_one() for RUNNING
        running_stopped = self._delete_one(trigger_id)
        
        self.logger.info(f"DELETE_ALL: TERMINATED {deleted_count} pending, "
                        f"running_stopped={running_stopped}")
        
        # 3. SINGLE EVENT - Complete status
        with self.app.app_context():
            trigger_cmd = Command.query.get(trigger_id)
            event_data = {
            "deleted_count": deleted_count,
            "running_stopped": running_stopped,
            "trigger_id": trigger_id,
            "sender": trigger_cmd.sender_phone
        }
        self._emit_event("PUMP_CLEARED_ALL", event_data)

    def _get_queue_position(self, cmd_id: int) -> int:
        """Position in QUEUED/ABORTED queue"""
        with self.app.app_context():
            cmd = Command.query.get(cmd_id)
            if cmd.status not in [CommandStatus.QUEUED, CommandStatus.ABORTED]:
                return 0
        
            ahead_count = Command.query.filter(
                Command.status.in_([CommandStatus.QUEUED, CommandStatus.ABORTED]),
                Command.priority < cmd.priority,
                or_(Command.priority == cmd.priority, Command.created_at < cmd.created_at)
            ).count()
        return ahead_count + 1