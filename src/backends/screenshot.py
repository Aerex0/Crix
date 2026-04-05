"""
Screenshot backend using grim (Wayland-native).

grim is a simple screenshot tool for Wayland compositors.
"""

import subprocess
import tempfile
import os
from typing import Optional


def capture_screen(
    output_path: Optional[str] = None,
    region: str = "full",
    width: int = 1920,
    height: int = 1080,
) -> str:
    """
    Capture a screenshot using grim.

    Args:
        output_path: Path to save the screenshot (auto-generated if None)
        region: 'full', 'top', 'bottom', 'left', 'right', or custom 'x,y wxh'
        width: Screen width (for region calculations)
        height: Screen height (for region calculations)

    Returns:
        Path to the saved screenshot

    Raises:
        RuntimeError: If screenshot capture fails
    """
    # Generate output path if not provided
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)

    # Calculate geometry for predefined regions
    region_map = {
        "full": None,  # No -g flag = full screen
        "top": f"0,0 {width}x{height // 2}",
        "bottom": f"0,{height // 2} {width}x{height // 2}",
        "left": f"0,0 {width // 2}x{height}",
        "right": f"{width // 2},0 {width // 2}x{height}",
    }

    geometry = region_map.get(region)

    # If not a predefined region, check if it's a custom geometry
    if geometry is None and region not in region_map:
        # Assume it's a custom geometry string like "100,100 800x600"
        geometry = region

    # Build command - try grim first, fallback to gnome-screenshot
    cmd = ["grim"]
    if geometry:
        cmd.extend(["-g", geometry])
    cmd.append(output_path)

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        # Fallback to gnome-screenshot for GNOME Wayland
        if geometry:
            # gnome-screenshot doesn't support custom regions easily
            raise RuntimeError(
                f"grim failed and gnome-screenshot doesn't support regions: {result.stderr.strip()}"
            )
        cmd = ["gnome-screenshot", "-f", output_path]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Screenshot failed: {result.stderr.strip()}")

    return output_path


def capture_region_interactive() -> str:
    """
    Capture a region selected interactively using slurp + grim.

    Requires slurp to be installed.

    Returns:
        Path to the saved screenshot

    Raises:
        RuntimeError: If capture fails
    """
    # Use slurp to select region
    slurp_result = subprocess.run(["slurp"], capture_output=True, text=True)

    if slurp_result.returncode != 0:
        raise RuntimeError("Region selection cancelled or slurp not installed")

    geometry = slurp_result.stdout.strip()

    # Create temp file
    fd, output_path = tempfile.mkstemp(suffix=".png")
    os.close(fd)

    # Capture the selected region
    result = subprocess.run(
        ["grim", "-g", geometry, output_path], capture_output=True, text=True
    )

    if result.returncode != 0:
        raise RuntimeError(f"grim failed: {result.stderr.strip()}")

    return output_path


def capture_window(window_class: Optional[str] = None) -> str:
    """
    Capture a specific window.

    Note: This is a simplified implementation. For proper window capture
    on Wayland, you'd typically need compositor-specific tools.

    Args:
        window_class: Window class to capture (not fully supported on Wayland)

    Returns:
        Path to the saved screenshot
    """
    # On Wayland, direct window capture is compositor-specific
    # Fall back to interactive region selection
    return capture_region_interactive()
