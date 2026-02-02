# app/tests/test_auth.py

def test_login_success(client, admin_token):
    # admin_token fixture already logs in successfully
    # If we reached here, login worked
    assert admin_token is not None
    assert isinstance(admin_token, str)

def test_login_fail(client):
    resp = client.post("/auth/login", data={
        "username": "noone@example.com",
        "password": "bad"
    })
    assert resp.status_code == 400
