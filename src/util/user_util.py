def user_to_dict(user):
    d = user.__dict__.copy()
    d.pop("password", None)
    return d
