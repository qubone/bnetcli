from bnetcli import config


def test_load_config_auto_creates(monkeypatch, tmp_path):
    # Point config file path to tmp and home to tmp to avoid touching real FS
    monkeypatch.setattr(config, "HOME_DIR", tmp_path)
    monkeypatch.setattr(config, "CONFIG_FILE_PATH", tmp_path / "cfg.yml")

    # Ensure file does not exist, call loader
    if (tmp_path / "cfg.yml").exists():
        (tmp_path / "cfg.yml").unlink()

    bcfg = config.BnetConfig.resolve(config.load_config())
    assert bcfg is not None
    assert hasattr(bcfg, "wine_prefix")


def test_detect_latest_proton_in_config(tmp_path):
    d = tmp_path / "compat"
    (d / "GE-Proton1-0").mkdir(parents=True)
    (d / "GE-Proton2-1").mkdir(parents=True)
    latest = config.detect_latest_proton(d)
    assert latest.name.startswith("GE-Proton2")
