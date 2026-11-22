"""Pipeline self-test: records the midterm slide page (no website needed).
python3 final/video/tools/record.py final/video/scenes/_selftest.py
"""
from pathlib import Path

PAGE = (Path(__file__).resolve().parents[3] / "slides" / "index.html").as_uri()


async def run(d):
    await d.goto(PAGE, wait=0.5)
    d.cap("這是錄影流程的自我測試", "This is a self-test of the recording pipeline")
    await d.wait(2)
    d.cap("按右鍵切換到下一張投影片", "Pressing the right arrow moves to the next slide")
    await d.press("ArrowRight", after=1.5)
    await d.press("ArrowRight", after=1.5)
    d.cap("滑鼠移動與點擊都會顯示游標和點擊效果", "Mouse moves and clicks show a visible cursor and ripple")
    await d.click("section.slide.on h2, section.slide.on h1", after=1.2)
    await d.highlight("section.slide.on h2, section.slide.on h1", sec=1.5)
    d.end_cap()
