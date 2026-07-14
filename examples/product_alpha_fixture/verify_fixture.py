from fixture_app import normalize_user_input


expected = "controllergate"
observed = normalize_user_input(" ControllerGate ")
raise SystemExit(0 if observed == expected else 1)
