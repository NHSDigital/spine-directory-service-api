import uuid


def get_uuid():
    """Generate a UUID suitable for sending in messages to Spine.

    :return: A string representation of the UUID.
    """
    return str(uuid.uuid4()).upper()
