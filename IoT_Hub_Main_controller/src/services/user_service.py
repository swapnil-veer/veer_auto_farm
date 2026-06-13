from werkzeug.security import check_password_hash


class UserService:
    """
    Handles:
    - User lookup
    - Authentication (SMS + Web)
    - Authorization (permissions)
    """

    def __init__(self, user_repo):
        self.repo = user_repo

    # -----------------------------------------
    # Identity / lookup
    # -----------------------------------------

    def get_by_phone(self, phone: str):
        return self.repo.get_by_phone(phone)

    def get_by_id(self, user_id: int):
        return self.repo.get_by_id(user_id)

    def get_by_email(self, email: str):
        return self.repo.get_by_email(email)

    # -----------------------------------------
    # Authentication
    # -----------------------------------------

    def authenticate_sms(self, phone: str):
        """
        SMS-based authentication:
        phone number = identity
        """
        user = self.get_by_phone(phone)
        if user and user.is_active:
            return user
        return None

    def authenticate_web(self, email: str, password: str):
        """
        Web-based authentication
        """
        user = self.get_by_email(email)

        if user and user.is_active:
            if user.password_hash and check_password_hash(user.password_hash, password):
                return user

        return None

    # -----------------------------------------
    # Authorization
    # -----------------------------------------

    def can_execute(self, user, command_type) -> bool:
        """
        Decide if user can execute command
        """

        if not user or not user.is_active:
            return False

        # Admin can do everything
        if user.role == "admin":
            return True

        # Operator rules
        if user.role == "operator":
            return True  # for now allow everything

        # Viewer rules
        if user.role == "viewer":
            return command_type == "STATUS"

        return False