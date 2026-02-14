"""
Example script demonstrating authentication API usage
"""

import requests
from typing import Optional

# Base API URL
BASE_URL = "http://localhost:8000/api/v1"


class ExploritoClient:
    """
    Simple client for interacting with Explorito API
    """

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None

    def register(
        self,
        email: str,
        password: str,
        display_name: str,
        role: str = "child",
        date_of_birth: Optional[str] = None,
        parent_email: Optional[str] = None,
    ) -> dict:
        """
        Register a new user

        Args:
            email: User email
            password: Password (min 8 chars, must include letter and digit)
            display_name: Display name
            role: User role (admin, parent, child)
            date_of_birth: Date in YYYY-MM-DD format
            parent_email: Parent's email (for children)

        Returns:
            User data with profile
        """
        data = {
            "email": email,
            "password": password,
            "display_name": display_name,
            "role": role,
        }

        if date_of_birth:
            data["date_of_birth"] = date_of_birth

        if parent_email:
            data["parent_email"] = parent_email

        response = requests.post(f"{self.base_url}/auth/register", json=data)
        response.raise_for_status()
        return response.json()

    def login(self, email: str, password: str) -> dict:
        """
        Login and store tokens

        Args:
            email: User email
            password: User password

        Returns:
            Token data
        """
        data = {"email": email, "password": password}
        response = requests.post(f"{self.base_url}/auth/login", json=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data.get("refresh_token")

        return token_data

    def get_current_user(self) -> dict:
        """
        Get current authenticated user info

        Returns:
            User data with profile
        """
        if not self.access_token:
            raise ValueError("Not authenticated. Please login first.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}/auth/me", headers=headers)
        response.raise_for_status()
        return response.json()

    def refresh_access_token(self) -> dict:
        """
        Refresh the access token

        Returns:
            New token data
        """
        if not self.refresh_token:
            raise ValueError("No refresh token available. Please login first.")

        data = {"refresh_token": self.refresh_token}
        response = requests.post(f"{self.base_url}/auth/refresh", json=data)
        response.raise_for_status()

        token_data = response.json()
        self.access_token = token_data["access_token"]

        return token_data

    def logout(self) -> None:
        """
        Logout (clear tokens)
        """
        if not self.access_token:
            raise ValueError("Not authenticated.")

        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.post(f"{self.base_url}/auth/logout", headers=headers)
        response.raise_for_status()

        # Clear local tokens
        self.access_token = None
        self.refresh_token = None


def main():
    """
    Example usage of the Explorito authentication API
    """
    client = ExploritoClient()

    print("=" * 60)
    print("Explorito Authentication API Example")
    print("=" * 60)

    # Example 1: Register a parent
    print("\n1. Registering a parent...")
    try:
        parent_data = client.register(
            email="john.doe@example.com",
            password="SecureParent123",
            display_name="John Doe",
            role="parent",
            date_of_birth="1985-03-15",
        )
        print(f"   ✓ Parent registered: {parent_data['email']}")
        print(f"   Profile: {parent_data['profile']['display_name']}")
    except requests.HTTPError as e:
        print(f"   ✗ Registration failed: {e.response.json()}")

    # Example 2: Register a child
    print("\n2. Registering a child...")
    try:
        child_data = client.register(
            email="alice.doe@example.com",
            password="SecureChild123",
            display_name="Alice Doe",
            role="child",
            date_of_birth="2015-06-20",
            parent_email="john.doe@example.com",
        )
        print(f"   ✓ Child registered: {child_data['email']}")
        print(f"   Profile: {child_data['profile']['display_name']}")
    except requests.HTTPError as e:
        print(f"   ✗ Registration failed: {e.response.json()}")

    # Example 3: Login as parent
    print("\n3. Logging in as parent...")
    try:
        token_data = client.login("john.doe@example.com", "SecureParent123")
        print(f"   ✓ Login successful")
        print(f"   Token type: {token_data['token_type']}")
        print(f"   Expires in: {token_data['expires_in']} seconds")
        print(f"   Access token: {token_data['access_token'][:50]}...")
    except requests.HTTPError as e:
        print(f"   ✗ Login failed: {e.response.json()}")

    # Example 4: Get current user info
    print("\n4. Getting current user info...")
    try:
        user_data = client.get_current_user()
        print(f"   ✓ User: {user_data['email']}")
        print(f"   Role: {user_data['role']}")
        print(f"   Display name: {user_data['profile']['display_name']}")
        print(f"   Active: {user_data['is_active']}")
    except requests.HTTPError as e:
        print(f"   ✗ Failed to get user info: {e.response.json()}")

    # Example 5: Refresh token
    print("\n5. Refreshing access token...")
    try:
        new_token_data = client.refresh_access_token()
        print(f"   ✓ Token refreshed successfully")
        print(f"   New access token: {new_token_data['access_token'][:50]}...")
    except requests.HTTPError as e:
        print(f"   ✗ Token refresh failed: {e.response.json()}")

    # Example 6: Logout
    print("\n6. Logging out...")
    try:
        client.logout()
        print(f"   ✓ Logged out successfully")
    except requests.HTTPError as e:
        print(f"   ✗ Logout failed: {e.response.json()}")

    # Example 7: Try to access protected endpoint after logout
    print("\n7. Attempting to access protected endpoint after logout...")
    try:
        client.get_current_user()
        print(f"   ✗ Should have failed!")
    except ValueError as e:
        print(f"   ✓ Access denied (expected): {e}")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
