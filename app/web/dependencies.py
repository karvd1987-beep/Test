from app.bootstrap import container


def get_container() -> dict:
    return container.as_dict()
