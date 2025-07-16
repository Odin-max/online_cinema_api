import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
def test_create_user():
    user = User.objects.create_user(email="Test@Example.COM", password="password123")
    assert user.email == "Test@example.com"
    assert user.check_password("password123")
    assert user.is_staff is False
    assert user.is_superuser is False


@pytest.mark.django_db
def test_create_user_no_email():
    with pytest.raises(ValueError) as excinfo:
        User.objects.create_user(email="", password="password123")
    assert "Email" in str(excinfo.value)


@pytest.mark.django_db
def test_create_superuser():
    admin = User.objects.create_superuser(email="admin@example.com", password="adminpass")
    assert admin.email == "admin@example.com"
    assert admin.check_password("adminpass")
    assert admin.is_staff is True
    assert admin.is_superuser is True


@pytest.mark.django_db
def test_create_superuser_without_staff_flag():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin2@example.com",
            password="adminpass",
            is_staff=False
        )


@pytest.mark.django_db
def test_create_superuser_without_superuser_flag():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            email="admin3@example.com",
            password="adminpass",
            is_superuser=False
        )


def test_str_returns_email():
    user = User(email="user@example.com")
    assert str(user) == "user@example.com"
