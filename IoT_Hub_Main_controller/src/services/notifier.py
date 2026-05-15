class Notifier:
    """
    Abstract notification interface.
    """

    def send(self, recipient: str, message: str, meta: dict | None = None):
        raise NotImplementedError