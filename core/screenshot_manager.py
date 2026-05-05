"""Screenshot management: capture on failure, visual regression comparison."""

import os
import time
from pathlib import Path
from datetime import datetime
from utils.logger import log


class ScreenshotManager:
    """Manages screenshots for test failures and visual regression."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = Path(reports_dir)
        self.screenshots_dir = self.reports_dir / "screenshots"
        self.baseline_dir = self.reports_dir / "visual_baseline"
        self.diff_dir = self.reports_dir / "visual_diff"

    def capture_on_failure(self, page, step_id: str, page_id: str, error_msg: str = "") -> str:
        """Capture screenshot when a test step fails."""
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"FAIL_{page_id}_{step_id}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        try:
            page.screenshot(path=str(filepath), full_page=True)
            log.info(f"Da chup man hinh loi: {filepath}")
            return str(filepath)
        except Exception as e:
            log.error(f"Khong the chup man hinh: {e}")
            return ""

    def capture_step(self, page, step_id: str, page_id: str) -> str:
        """Capture screenshot for a specific step (for reports)."""
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"STEP_{page_id}_{step_id}_{timestamp}.png"
        filepath = self.screenshots_dir / filename
        try:
            page.screenshot(path=str(filepath))
            return str(filepath)
        except Exception:
            return ""

    def save_baseline(self, page, page_id: str) -> str:
        """Save a baseline screenshot for visual regression."""
        self.baseline_dir.mkdir(parents=True, exist_ok=True)
        filepath = self.baseline_dir / f"{page_id}_baseline.png"
        try:
            page.screenshot(path=str(filepath), full_page=True)
            log.info(f"Da luu baseline: {filepath}")
            return str(filepath)
        except Exception as e:
            log.error(f"Khong the luu baseline: {e}")
            return ""

    def compare_visual(self, page, page_id: str, threshold: float = 0.05) -> dict:
        """Compare current page with baseline screenshot.

        Returns dict with:
            match: bool - True if images match within threshold
            diff_percentage: float - percentage of different pixels
            diff_image: str - path to diff image (if different)
            baseline_path: str
            current_path: str
        """
        self.diff_dir.mkdir(parents=True, exist_ok=True)
        baseline_path = self.baseline_dir / f"{page_id}_baseline.png"

        if not baseline_path.exists():
            return {
                "match": False,
                "diff_percentage": -1,
                "error": f"Khong tim thay baseline: {baseline_path}",
                "baseline_path": "",
                "current_path": "",
                "diff_image": "",
            }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_path = self.diff_dir / f"{page_id}_current_{timestamp}.png"
        page.screenshot(path=str(current_path), full_page=True)

        try:
            diff_pct, diff_img_path = self._compare_images(
                str(baseline_path), str(current_path), page_id, timestamp
            )
            match = diff_pct <= threshold
            return {
                "match": match,
                "diff_percentage": diff_pct,
                "baseline_path": str(baseline_path),
                "current_path": str(current_path),
                "diff_image": diff_img_path,
                "error": "",
            }
        except Exception as e:
            return {
                "match": False,
                "diff_percentage": -1,
                "error": str(e),
                "baseline_path": str(baseline_path),
                "current_path": str(current_path),
                "diff_image": "",
            }

    def _compare_images(self, baseline_path: str, current_path: str,
                        page_id: str, timestamp: str) -> tuple:
        """Compare two images pixel-by-pixel. Returns (diff_percentage, diff_image_path)."""
        try:
            from PIL import Image, ImageChops
        except ImportError:
            log.warning("Pillow chua duoc cai dat. Dung: pip install Pillow")
            return (0.0, "")

        img1 = Image.open(baseline_path).convert("RGB")
        img2 = Image.open(current_path).convert("RGB")

        # Resize to same dimensions if needed
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)

        diff = ImageChops.difference(img1, img2)
        diff_pixels = sum(1 for px in diff.getdata() if sum(px) > 30)
        total_pixels = img1.size[0] * img1.size[1]
        diff_pct = diff_pixels / total_pixels if total_pixels > 0 else 0

        diff_img_path = ""
        if diff_pct > 0:
            diff_img_path = str(self.diff_dir / f"{page_id}_diff_{timestamp}.png")
            diff.save(diff_img_path)

        return (diff_pct, diff_img_path)
