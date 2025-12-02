"""Tests for ndev-settings CLI utilities."""

import sys

import yaml

from ndev_settings._cli import main_reset_values, reset_values_to_defaults


class TestResetValuesToDefaults:
    """Tests for reset_values_to_defaults function."""

    def test_reset_modified_values(self, tmp_path):
        """Test that modified values are reset to defaults."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting1": {
                            "value": "modified",
                            "default": "original",
                        },
                        "setting2": {"value": 100, "default": 50},
                    }
                }
            )
        )

        result = reset_values_to_defaults(settings_file)

        assert result is True
        with open(settings_file) as f:
            updated = yaml.safe_load(f)
        assert updated["TestGroup"]["setting1"]["value"] == "original"
        assert updated["TestGroup"]["setting2"]["value"] == 50

    def test_no_changes_when_values_match_defaults(self, tmp_path):
        """Test that no changes are made when values already match defaults."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting1": {
                            "value": "original",
                            "default": "original",
                        },
                    }
                }
            )
        )

        result = reset_values_to_defaults(settings_file)

        assert result is False

    def test_missing_file_returns_false(self, tmp_path, capsys):
        """Test that missing file returns False and prints message."""
        missing_file = tmp_path / "nonexistent.yaml"

        result = reset_values_to_defaults(missing_file)

        assert result is False
        captured = capsys.readouterr()
        assert "Settings file not found" in captured.out

    def test_empty_file_returns_false(self, tmp_path):
        """Test that empty file returns False."""
        settings_file = tmp_path / "empty.yaml"
        settings_file.write_text("")

        result = reset_values_to_defaults(settings_file)

        assert result is False

    def test_settings_without_default_key_unchanged(self, tmp_path):
        """Test that settings without 'default' key are not modified."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting_no_default": {"value": "something"},
                    }
                }
            )
        )

        result = reset_values_to_defaults(settings_file)

        assert result is False

    def test_settings_without_value_key_unchanged(self, tmp_path):
        """Test that settings without 'value' key are not modified."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting_no_value": {"default": "something"},
                    }
                }
            )
        )

        result = reset_values_to_defaults(settings_file)

        assert result is False

    def test_accepts_string_path(self, tmp_path):
        """Test that string paths are accepted."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting1": {
                            "value": "modified",
                            "default": "original",
                        },
                    }
                }
            )
        )

        result = reset_values_to_defaults(str(settings_file))

        assert result is True


class TestMainResetValues:
    """Tests for main_reset_values CLI entry point."""

    def test_no_args_shows_usage(self, monkeypatch, capsys):
        """Test that no arguments shows usage and returns 1."""
        monkeypatch.setattr(sys, "argv", ["reset-settings-values"])

        result = main_reset_values()

        assert result == 1
        captured = capsys.readouterr()
        assert "Usage:" in captured.out
        assert "pre-commit hook" in captured.out

    def test_single_file_modified(self, tmp_path, monkeypatch, capsys):
        """Test processing a single file that needs modification."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting1": {
                            "value": "modified",
                            "default": "original",
                        },
                    }
                }
            )
        )
        monkeypatch.setattr(
            sys, "argv", ["reset-settings-values", str(settings_file)]
        )

        result = main_reset_values()

        assert result == 1
        captured = capsys.readouterr()
        assert "WARNING" in captured.out
        assert "re-stage" in captured.out

    def test_single_file_unchanged(self, tmp_path, monkeypatch):
        """Test processing a single file that doesn't need modification."""
        settings_file = tmp_path / "settings.yaml"
        settings_file.write_text(
            yaml.dump(
                {
                    "TestGroup": {
                        "setting1": {
                            "value": "original",
                            "default": "original",
                        },
                    }
                }
            )
        )
        monkeypatch.setattr(
            sys, "argv", ["reset-settings-values", str(settings_file)]
        )

        result = main_reset_values()

        assert result == 0

    def test_multiple_files(self, tmp_path, monkeypatch, capsys):
        """Test processing multiple files."""
        file1 = tmp_path / "settings1.yaml"
        file2 = tmp_path / "settings2.yaml"
        file1.write_text(
            yaml.dump(
                {
                    "Group1": {
                        "s1": {"value": "modified", "default": "original"}
                    }
                }
            )
        )
        file2.write_text(
            yaml.dump(
                {
                    "Group2": {
                        "s2": {"value": "original", "default": "original"}
                    }
                }
            )
        )
        monkeypatch.setattr(
            sys, "argv", ["reset-settings-values", str(file1), str(file2)]
        )

        result = main_reset_values()

        assert result == 1  # At least one file was modified
        captured = capsys.readouterr()
        assert "Resetting Group1.s1" in captured.out

    def test_missing_file_in_list(self, tmp_path, monkeypatch, capsys):
        """Test that missing files are handled gracefully."""
        existing_file = tmp_path / "exists.yaml"
        existing_file.write_text(
            yaml.dump(
                {"Group": {"s": {"value": "original", "default": "original"}}}
            )
        )
        missing_file = tmp_path / "missing.yaml"

        monkeypatch.setattr(
            sys,
            "argv",
            ["reset-settings-values", str(existing_file), str(missing_file)],
        )

        result = main_reset_values()

        assert result == 0  # No modifications made
        captured = capsys.readouterr()
        assert "not found" in captured.out
