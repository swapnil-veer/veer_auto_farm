from app import db
from database.models.command import Command, CommandStatus, CommandType

class CommandRepository:
    def __init__(self, app):
        self.app = app

    def create(self, **fields) -> Command:
        with self.app.app_context():
            cmd = Command(**fields)
            db.session.add(cmd)
            db.session.commit()
            return cmd

    def get(self, cmd_id: int) -> Command | None:
            with self.app.app_context():
                return Command.query.get(cmd_id)

    def update(self, cmd_id: int, **updates):
        with self.app.app_context():
            Command.query.filter_by(id=cmd_id).update(updates)
            db.session.commit()

    def get_next_queued(self):
        with self.app.app_context():
            return (
            Command.query
            .filter_by(status=CommandStatus.QUEUED)
            .order_by(Command.priority, Command.created_at)
            .first()
            )

    def get_waiting_for_power(self):
        with self.app.app_context():
            return (
            Command.query
            .filter_by(status=CommandStatus.ABORTED)
            .order_by(Command.priority, Command.created_at)
            .first()
            )