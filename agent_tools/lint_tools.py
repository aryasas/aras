import subprocess


def run_linter(path: str) -> str:
    try:
        result = subprocess.run(
            ["flake8", path, "--max-line-length=100"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return f"✅ No linting issues found in {path}"
        return f"⚠️ Linting issues:\n{result.stdout}"
    except FileNotFoundError:
        return "flake8 not installed. Run: pip install flake8"
    except Exception as e:
        return f"Linter error: {str(e)}"
