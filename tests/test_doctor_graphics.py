from bnetcli import doctor


def test_check_graphics_all_ok(monkeypatch, capsys):
    # Simulate everything OK
    monkeypatch.setattr(doctor, "check_vulkan", lambda: True)
    monkeypatch.setattr(doctor, "get_vulkan_icds", lambda: "icd1:icd2")
    monkeypatch.setattr(doctor, "detect_gpu", lambda: "Nvidia")

    # Simulate glxinfo present and returning OpenGL version
    monkeypatch.setattr(doctor, "_binary_exists", lambda name: True)
    monkeypatch.setattr(doctor, "_run_quiet", lambda cmd: (0, "OpenGL version string: 4.6"))

    # Should not raise
    doctor.check_graphics()
