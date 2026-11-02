from workstation.connections.check import check_endpoint


def test_check_endpoint_lists_models_then_requests_short_completion():
    calls = []

    def fake_http(method, url, *, json, timeout):
        calls.append((method, url, json, timeout))
        return 200, b"{}"

    result = check_endpoint("http://localhost:8080/", "demo", timeout_s=4, http=fake_http)

    assert result == {
        "passed": True,
        "steps": {
            "list_models": {"passed": True, "status": 200},
            "completion": {"passed": True, "status": 200},
        },
    }
    assert calls == [
        ("GET", "http://localhost:8080/v1/models", None, 4),
        (
            "POST",
            "http://localhost:8080/v1/chat/completions",
            {
                "model": "demo",
                "messages": [{"role": "user", "content": "Reply with OK."}],
                "max_tokens": 16,
            },
            4,
        ),
    ]


def test_check_endpoint_reports_http_status_and_continues_after_failure():
    statuses = iter((503, 201))

    def fake_http(method, url, *, json, timeout):
        return next(statuses), b"{}"

    result = check_endpoint("http://endpoint", "demo", http=fake_http)

    assert result["passed"] is False
    assert result["steps"]["list_models"] == {
        "passed": False,
        "status": 503,
        "error": "HTTP 503",
    }
    assert result["steps"]["completion"] == {"passed": True, "status": 201}


def test_check_endpoint_reports_request_error_for_its_step():
    def fake_http(method, url, *, json, timeout):
        if method == "GET":
            raise TimeoutError("timed out")
        return 200, b"{}"

    result = check_endpoint("http://endpoint", "demo", http=fake_http)

    assert result["passed"] is False
    assert result["steps"]["list_models"] == {"passed": False, "error": "timed out"}
    assert result["steps"]["completion"] == {"passed": True, "status": 200}
