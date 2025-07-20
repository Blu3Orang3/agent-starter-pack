# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import platform
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.cli.utils.platform_utils import (
    check_command_exists,
    create_platform_specific_scripts,
    ensure_utf8_encoding,
    get_npm_install_command,
    get_platform_info,
    get_python_executable,
    get_shell_command,
    is_linux,
    is_macos,
    is_windows,
    suggest_make_installation,
    suggest_uv_installation,
)


class TestPlatformDetection(unittest.TestCase):
    """Test platform detection functions."""

    def test_platform_detection_functions(self) -> None:
        """Test that platform detection functions work correctly."""
        system = platform.system()

        if system == "Windows":
            self.assertTrue(is_windows())
            self.assertFalse(is_macos())
            self.assertFalse(is_linux())
        elif system == "Darwin":
            self.assertFalse(is_windows())
            self.assertTrue(is_macos())
            self.assertFalse(is_linux())
        elif system == "Linux":
            self.assertFalse(is_windows())
            self.assertFalse(is_macos())
            self.assertTrue(is_linux())

    def test_get_platform_info(self) -> None:
        """Test platform info retrieval."""
        system, arch, version = get_platform_info()
        self.assertIsInstance(system, str)
        self.assertIsInstance(arch, str)
        self.assertIsInstance(version, str)
        self.assertIn(system, ["Windows", "Darwin", "Linux"])


class TestCrossPlatformCommands(unittest.TestCase):
    """Test cross-platform command generation."""

    def test_get_shell_command_windows(self) -> None:
        """Test shell command generation for Windows."""
        with patch("src.cli.utils.platform_utils.is_windows", return_value=True):
            result = get_shell_command("echo hello")
            self.assertEqual(result, ["cmd", "/c", "echo hello"])

    def test_get_shell_command_unix(self) -> None:
        """Test shell command generation for Unix-like systems."""
        with patch("src.cli.utils.platform_utils.is_windows", return_value=False):
            result = get_shell_command("echo hello")
            self.assertEqual(result, ["sh", "-c", "echo hello"])

    def test_get_npm_install_command_windows(self) -> None:
        """Test npm install command for Windows."""
        with patch("src.cli.utils.platform_utils.is_windows", return_value=True):
            result = get_npm_install_command("frontend")
            self.assertEqual(result, "cd frontend && npm install")

    def test_get_npm_install_command_unix(self) -> None:
        """Test npm install command for Unix-like systems."""
        with patch("src.cli.utils.platform_utils.is_windows", return_value=False):
            result = get_npm_install_command("frontend")
            self.assertEqual(result, "npm --prefix frontend install")


class TestCommandExistence(unittest.TestCase):
    """Test command existence checking."""

    def test_check_command_exists_python(self) -> None:
        """Test that Python command exists."""
        # Python should exist since we're running this test
        self.assertTrue(
            check_command_exists("python")
            or check_command_exists("python3")
            or check_command_exists("py")
        )

    def test_check_command_exists_nonexistent(self) -> None:
        """Test that non-existent command returns False."""
        self.assertFalse(check_command_exists("definitely_not_a_real_command_12345"))

    def test_get_python_executable(self) -> None:
        """Test Python executable path retrieval."""
        executable = get_python_executable()
        self.assertIsInstance(executable, str)
        self.assertTrue(Path(executable).exists())


class TestInstallationSuggestions(unittest.TestCase):
    """Test installation suggestion functions."""

    def test_suggest_make_installation_returns_string(self) -> None:
        """Test that make installation suggestions return strings."""
        suggestion = suggest_make_installation()
        self.assertIsInstance(suggestion, str)
        self.assertGreater(len(suggestion), 50)  # Should be a substantial message

    def test_suggest_uv_installation_returns_string(self) -> None:
        """Test that uv installation suggestions return strings."""
        suggestion = suggest_uv_installation()
        self.assertIsInstance(suggestion, str)
        self.assertGreater(len(suggestion), 50)  # Should be a substantial message

    @patch("src.cli.utils.platform_utils.is_windows")
    def test_suggest_make_installation_windows(
        self, mock_is_windows: MagicMock
    ) -> None:
        """Test Windows-specific make installation suggestions."""
        mock_is_windows.return_value = True
        suggestion = suggest_make_installation()
        self.assertIn("Chocolatey", suggestion)
        self.assertIn("Winget", suggestion)
        self.assertIn("Scoop", suggestion)

    @patch("src.cli.utils.platform_utils.is_macos")
    @patch("src.cli.utils.platform_utils.is_windows")
    def test_suggest_make_installation_macos(
        self, mock_is_windows: MagicMock, mock_is_macos: MagicMock
    ) -> None:
        """Test macOS-specific make installation suggestions."""
        mock_is_windows.return_value = False
        mock_is_macos.return_value = True
        suggestion = suggest_make_installation()
        self.assertIn("Homebrew", suggestion)
        self.assertIn("xcode-select", suggestion)


class TestUTF8Encoding(unittest.TestCase):
    """Test UTF-8 encoding functionality."""

    def test_ensure_utf8_encoding(self) -> None:
        """Test UTF-8 encoding setup."""
        # This function modifies environment variables
        original_env = os.environ.copy()
        try:
            ensure_utf8_encoding()
            # Function should complete without error
            self.assertTrue(True)
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)

    @patch("src.cli.utils.platform_utils.is_windows")
    def test_ensure_utf8_encoding_windows(self, mock_is_windows: MagicMock) -> None:
        """Test UTF-8 encoding setup on Windows."""
        mock_is_windows.return_value = True
        original_env = os.environ.copy()
        try:
            # Clear relevant env vars
            os.environ.pop("PYTHONIOENCODING", None)
            os.environ.pop("PYTHONUTF8", None)

            ensure_utf8_encoding()

            self.assertEqual(os.environ.get("PYTHONIOENCODING"), "utf-8")
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


class TestPlatformSpecificScripts(unittest.TestCase):
    """Test platform-specific script generation."""

    def test_create_platform_specific_scripts(self) -> None:
        """Test that platform-specific scripts are created correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Should not raise an exception
            create_platform_specific_scripts(project_path)

            # Check that files were created
            batch_file = project_path / "build.bat"
            ps_file = project_path / "build.ps1"

            self.assertTrue(batch_file.exists())
            self.assertTrue(ps_file.exists())

            # Check file contents
            with open(batch_file, encoding="utf-8") as f:
                batch_content = f.read()
                self.assertIn("@echo off", batch_content)
                self.assertIn("install", batch_content)
                self.assertIn("playground", batch_content)

            with open(ps_file, encoding="utf-8") as f:
                ps_content = f.read()
                self.assertIn("param(", ps_content)
                self.assertIn("switch", ps_content)
                self.assertIn("install", ps_content)


class TestFileEncodingFixes(unittest.TestCase):
    """Test that file operations use proper encoding."""

    def test_file_operations_use_utf8_encoding(self) -> None:
        """Test that our utility functions properly handle UTF-8."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Test script creation with UTF-8 content
            create_platform_specific_scripts(project_path)

            # Try to read the files with UTF-8 encoding
            batch_file = project_path / "build.bat"
            ps_file = project_path / "build.ps1"

            # These should not raise encoding errors
            with open(batch_file, encoding="utf-8") as f:
                content = f.read()
                self.assertIsInstance(content, str)

            with open(ps_file, encoding="utf-8") as f:
                content = f.read()
                self.assertIsInstance(content, str)


@pytest.mark.integration
class TestIntegrationWindows(unittest.TestCase):
    """Integration tests specific to Windows functionality."""

    @unittest.skipUnless(platform.system() == "Windows", "Windows-specific test")
    def test_windows_batch_script_syntax(self) -> None:
        """Test that generated batch scripts have correct Windows syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            create_platform_specific_scripts(project_path)

            batch_file = project_path / "build.bat"
            with open(batch_file, encoding="utf-8") as f:
                content = f.read()

            # Check for Windows batch script markers
            self.assertIn("@echo off", content)
            self.assertIn("set SCRIPT_DIR=%~dp0", content)
            self.assertIn("cd /d", content)
            self.assertIn("goto", content)

    @unittest.skipUnless(platform.system() == "Windows", "Windows-specific test")
    def test_windows_powershell_script_syntax(self) -> None:
        """Test that generated PowerShell scripts have correct syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            create_platform_specific_scripts(project_path)

            ps_file = project_path / "build.ps1"
            with open(ps_file, encoding="utf-8") as f:
                content = f.read()

            # Check for PowerShell script markers
            self.assertIn("param(", content)
            self.assertIn("switch", content)
            self.assertIn("Set-Location", content)
            self.assertIn("Write-Host", content)


if __name__ == "__main__":
    unittest.main()
