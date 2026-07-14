# composition.py
from dotenv import load_dotenv
import os
import threading
from logging_config import logger
load_dotenv()

# Infrastructure
from infrastructure.gpio_seed import setup_gpio_runtime
from infrastructure.command_repository import CommandRepository
from infrastructure.pump_repository import PumpRepository
from infrastructure.sms_repository import SMSRepository
from infrastructure.phase_repository import PhaseRepository
from infrastructure.user_repository import UserRepository

# Hardware
APP_MODE = os.getenv("APP_MODE", "prod")

if APP_MODE == "local":
    from hardware.mock.mock_gpio import MockGPIO
    gpio = MockGPIO()
    from hardware.mock.mock_sim_modem import MockSIMModem as SIMModem
    from hardware.mock.mock_pump_gpio import MockPumpGPIO as PumpGPIO
    from hardware.mock.mock_phase_gpio import MockPhaseGPIO as PhaseGPIO
else:
    from hardware.gpio_rpi import RaspberryPiGPIO
    gpio = RaspberryPiGPIO()
    from hardware.sim_modem import SIMModem
    from hardware.pump_gpio import PumpGPIO
    from hardware.phase_gpio import PhaseGPIO
    from hardware.lcd_hw import LCDDriver 


# Services

from services.pump_service import PumpService
from services.pump_context import PumpContextManager
from services.phase_monitor import PhaseMonitor
from services.sim_service import SIMService
from services.sms_notifier import SMSNotifier
from services.command_engine import CommandEngine
from services.command_scheduler import CommandScheduler
from services.command_events import CommandEventEmitter
from services.logging_handler import EventLoggingHandler
from services.lcd_service import LCDService

# Controller
from main_controller import MainController

class ApplicationContext:
    """
    Holds references to all long-lived services.
    Useful for startup, shutdown, and diagnostics.
    """
    def __init__(self, app, scheduler, sim_service, phase_monitor):
        self.app = app
        self.scheduler = scheduler
        self.sim_service = sim_service
        self.phase_monitor = phase_monitor

def compose_application(app):
    """
    Composition root:
    - Build object graph
    - Wire dependencies
    - Start background services
    """

    logger.info("Composing application services...")
    
    setup_gpio_runtime(app, gpio)
    # -------------------------
    # Repositories (DB)
    # -------------------------
    command_repo = CommandRepository(app)
    pump_repo = PumpRepository(app)
    sms_repo = SMSRepository(app)
    phase_repo = PhaseRepository(app)
    user_repo = UserRepository(app)

    # -------------------------
    # Hardware adapters
    # -------------------------
    pump_id = pump_repo.get_default_pump_id()
    pump_pin = pump_repo.get_pump_gpio_pin(pump_id)
    pump_gpio = PumpGPIO(gpio, pump_pin)
    phase_gpio = PhaseGPIO()
    sim_modem = SIMModem()
    lcd_driver = LCDDriver()

    # -------------------------
    # Core services
    # -------------------------
    pump_service = PumpService(pump_gpio, pump_repo, pump_id)
    # pump_context = PumpContextManager(pump_service)

    phase_monitor = PhaseMonitor(
        gpio_reader=phase_gpio,
        repository=phase_repo, 
        poll_interval=1,
    )

    sim_service = SIMService(
        modem=sim_modem,
        user_repo=user_repo,
        sms_repo=sms_repo,
        poll_interval=60,
    )

    sms_notifier = SMSNotifier(sim_service)
  
    # -------------------------
    # Power abstraction
    # -------------------------
    power_service = phase_monitor # conforms to is_power_available()

    # -------------------------
    # Voluntary Services
    # -------------------------
    lcd_service = LCDService(
        lcd_driver=lcd_driver,
        command_repo=command_repo,
        sim_service=sim_service,
        power_service=power_service,
    )

    # -------------------------
    # Command orchestration
    # -------------------------
    event_emitter = CommandEventEmitter()

    command_engine = CommandEngine(
        # pump_context_manager=pump_context,
        pump_service = pump_service,
        power_service=power_service,
        command_repo=command_repo,
        event_emitter=event_emitter,
    )

    scheduler = CommandScheduler(
        engine=command_engine,
        command_repo=command_repo,
        poll_interval=60,
    )

    # -------------------------
    # Start background workers
    # -------------------------
    scheduler.start()


    # -------------------------
    # Main controller
    # -------------------------
    main_controller = MainController(
        scheduler=scheduler,
        command_engine=command_engine,
        power_service=power_service,
        sim_service=sim_service,
        notifier=sms_notifier,
    )

    event_emitter.register(main_controller.handle_event)
    # event_emitter.register(EventLoggingHandler.handle)
    event_emitter.register(lcd_service.handle_event)


    # sms polling thread
    main_controller.start_sms_polling()

    logger.info("Application composition complete.")

    return ApplicationContext(
        app=app,
        scheduler=scheduler,
        sim_service=sim_service,
        phase_monitor=phase_monitor,
        )