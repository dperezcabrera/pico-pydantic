from pico_ioc import component
from pico_pydantic import validate


@component
class UserService:
    """Service with validated methods."""

    @validate
    def create_user(self, name: str, email: str, age: int) -> dict:
        """Create a user with validated inputs.

        Args:
            name: User's full name (string required)
            email: User's email address (string required)
            age: User's age (integer required)
        """
        return {
            "name": name,
            "email": email,
            "age": age,
            "status": "active",
        }

    @validate
    def update_age(self, user_id: int, new_age: int) -> dict:
        """Update a user's age with type validation."""
        return {"user_id": user_id, "new_age": new_age, "updated": True}
