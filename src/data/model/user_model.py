class UserModel:
    def __init__(
        self,
        id,
        username,
        email,
        password,
        first_name,
        last_name,
        date_of_birth=None,
        gender=None,
        phone=None,
        address=None,
        current_latitude=None,
        current_longitude=None,
        current_diseases=None,
        role=None,
        is_active=True,
    ):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.gender = gender
        self.phone = phone
        self.address = address
        self.current_latitude = current_latitude
        self.current_longitude = current_longitude
        self.current_diseases = current_diseases
        self.role = role
        self.is_active = is_active

    @staticmethod
    def from_row(row):
        return UserModel(*row)
