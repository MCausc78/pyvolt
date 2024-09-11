import pyvolt


def test_flags():
    permissions = pyvolt.Permissions()
    assert permissions.value == 0

    permissions.manage_webhooks = True
    assert permissions.manage_webhooks is True
    assert permissions.value == 16777216

    permissions.manage_webhooks = False
    assert permissions.manage_webhooks is False
    assert permissions.value == 0

    permissions = pyvolt.Permissions(manage_webhooks=True)
    assert permissions.manage_webhooks is True
    assert permissions.value == 16777216

    permissions.manage_webhooks = False
    assert permissions.manage_webhooks is False
    assert permissions.value == 0
