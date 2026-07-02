import os


def get_required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise RuntimeError(f"{name} is required")

    return value


def get_bool_env(name: str, default: bool = False) -> bool:
    raw_value = os.getenv(name)

    if raw_value is None:
        return default

    return raw_value.strip().lower() in {"1", "true", "yes", "on"}


def get_admin_ids_from_env() -> set[int]:
    values = []
    admin_ids = os.getenv("ADMIN_IDS")
    admin_id = os.getenv("ADMIN_ID")

    if admin_ids:
        values.extend(admin_ids.split(","))

    if admin_id:
        values.append(admin_id)

    result = set()
    for value in values:
        value = value.strip()

        if not value:
            continue

        try:
            result.add(int(value))
        except ValueError:
            continue

    return result
