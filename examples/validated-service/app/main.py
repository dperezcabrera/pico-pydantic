from pico_boot import init

from .services import UserService


def main():
    container = init(modules=["app"])  # scans recursively

    service = container.get(UserService)

    # Valid input
    user = service.create_user(name="Alice", email="alice@example.com", age=30)
    print(f"Created user: {user}")

    # Valid update
    result = service.update_age(user_id=1, new_age=31)
    print(f"Updated: {result}")

    # Invalid input - will raise ValidationFailedError
    try:
        service.create_user(name="Bob", email="bob@example.com", age="not-a-number")
    except Exception as e:
        print(f"\nValidation error (expected): {e}")

    container.shutdown()


if __name__ == "__main__":
    main()
