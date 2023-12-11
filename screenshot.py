import subprocess
import logging
import os

def take_screenshot(url):
    """
    This function takes a URL, uses a subprocess to run a Node.js script 
    that takes a screenshot of the webpage at the URL, and saves it as 'screenshot.jpg'.
    It returns the exit code and the output of the subprocess.
    If an error occurs during the subprocess, it logs the error.
    """
    if os.path.exists("screenshot.jpg"):
        os.remove("screenshot.jpg")

    try:
        result = subprocess.run(
            ["node", "screenshot.cjs", url],
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return None, None
