from app.shared.events.bus import event_bus
from app.modules.authorization.application.handlers import handle_security_violation

def register_authorization(event_bus_instance) -> None:
    event_bus_instance.subscribe("SecurityViolationDetectedEvent", handle_security_violation)

register_authorization(event_bus)
