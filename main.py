import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
import random
from pathlib import Path
from PIL import Image

from config import OUTPUT_DIR, BASE_DIR
from src.asset_manager import AssetManager
from src.compositor import Compositor
from src.topic_manager import TopicManager
from src.llm_generator import LLMGenerator

import random

def run_test_mode():
    """Renders slides using local test_payload.json without triggering API requests."""
    print("🚀 Running in Offline Test Mode...")
    test_file = BASE_DIR / "test_payload.json"
    if not test_file.exists():
        print("❌ Error: test_payload.json not found!")
        sys.exit(1)

    with open(test_file, "r", encoding="utf-8") as f:
        payload = json.load(f)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUTPUT_DIR / f"test_run_{timestamp}"
    out_dir.mkdir(parents=True, exist_ok=True)

    asset_mgr = AssetManager()
    compositor = Compositor()

    # -------------------------------------------------------------
    # Pick ONE random background from assets/backgrounds for this run
    # -------------------------------------------------------------
    bg_folder = BASE_DIR / "assets" / "backgrounds"
    bg_files = [f.name for f in bg_folder.glob("*") if f.suffix.lower() in [".png", ".jpg", ".jpeg"]]

    if bg_files:
        chosen_bg = random.choice(bg_files)
        print(f"🎲 Selected random background for this run: {chosen_bg}")
        bg_image = asset_mgr.load_background_image(chosen_bg)
    else:
        # Fallback to payload setting if folder is empty
        bg_filename = payload.get("selected_background", "")
        bg_image = asset_mgr.load_background_image(bg_filename)

    # 1. Render Cover Slide
    cover_data = {"type": "cover", **payload["cover"]}
    cover_img = compositor.render_slide(cover_data, bg_image)
    cover_img.save(out_dir / "slide_00_cover.png")

    # 2. Render Question Slides (reusing the same bg_image)
    for idx, slide in enumerate(payload.get("slides", []), start=1):
        slide_img = compositor.render_slide(slide, bg_image)
        slide_img.save(out_dir / f"slide_{idx:02d}_{slide['type']}.png")

    # Save Payload Copy
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print(f"✨ Test slides generated in: {out_dir}")

def run_batch_mode(batch_size: int, questions_per_post: int):
    """Generates carousel posts via Gemini LLM and renders full slide decks."""
    print(f"🚀 Generating {batch_size} carousel post(s)...")
    topic_mgr = TopicManager()
    asset_mgr = AssetManager()
    compositor = Compositor()
    generator = LLMGenerator()

    available_bgs = asset_mgr.get_available_backgrounds()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = OUTPUT_DIR / f"batch_{timestamp}"
    batch_dir.mkdir(parents=True, exist_ok=True)

    for post_idx in range(1, batch_size + 1):
        print(f"\n--- Generating Post {post_idx}/{batch_size} ---")
        topics = topic_mgr.sample_topics(1)
        payload = generator.generate_post_payload(topics, available_bgs, questions_per_post)

        topic_slug = payload.get("topic_slug", f"post_{post_idx:02d}")
        post_dir = batch_dir / f"post_{post_idx:02d}_{topic_slug}"
        post_dir.mkdir(parents=True, exist_ok=True)

        bg_filename = payload.get("selected_background", "")
        bg_image = asset_mgr.load_background_image(bg_filename)

        # Render Cover
        cover_data = {"type": "cover", **payload["cover"]}
        cover_img = compositor.render_slide(cover_data, bg_image)
        cover_img.save(post_dir / "slide_00_cover.png")

        # Render Slides
        for idx, slide in enumerate(payload.get("slides", []), start=1):
            slide_img = compositor.render_slide(slide, bg_image)
            slide_img.save(post_dir / f"slide_{idx:02d}_{slide['type']}.png")

        with open(post_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

        print(f"✅ Saved post to: {post_dir}")

    print(f"\n🎉 Batch run complete! All outputs saved in: {batch_dir}")

def run_jobs_mode():
    """Generates carousel posts according to the JOBS list in job_config.py.
    Each job can force a specific mode/audience/slide_type and set its own
    batch count and slides-per-post."""
    from src.job_config import JOBS

    topic_mgr = TopicManager()
    asset_mgr = AssetManager()
    compositor = Compositor()
    generator = LLMGenerator()

    available_bgs = asset_mgr.get_available_backgrounds()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = OUTPUT_DIR / f"jobs_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    total_posts = sum(job["batches"] for job in JOBS)
    print(f"🚀 Running {len(JOBS)} job(s), {total_posts} post(s) total...")

    post_counter = 0
    for job in JOBS:
        label = job.get("label", "job")
        batches = job.get("batches", 1)
        questions = job.get("questions", 3)
        mode = job.get("mode")
        audience = job.get("audience")
        slide_type = job.get("slide_type")

        print(f"\n=== Job: {label} ({batches} batch(es), {questions} slide(s) each) ===")

        for i in range(1, batches + 1):
            post_counter += 1
            print(f"\n--- {label} post {i}/{batches} (overall #{post_counter}) ---")
            topics = topic_mgr.sample_topics(1)
            payload = generator.generate_post_payload(
                topics,
                available_bgs,
                questions,
                forced_mode_key=mode,
                forced_audience=audience,
                forced_slide_type=slide_type,
            )

            topic_slug = payload.get("topic_slug", f"post_{post_counter:02d}")
            post_dir = run_dir / f"{label}_{i:02d}_{topic_slug}"
            post_dir.mkdir(parents=True, exist_ok=True)

            bg_filename = payload.get("selected_background", "")
            bg_image = asset_mgr.load_background_image(bg_filename)

            cover_data = {"type": "cover", **payload["cover"]}
            cover_img = compositor.render_slide(cover_data, bg_image)
            cover_img.save(post_dir / "slide_00_cover.png")

            for idx, slide in enumerate(payload.get("slides", []), start=1):
                slide_img = compositor.render_slide(slide, bg_image)
                slide_img.save(post_dir / f"slide_{idx:02d}_{slide['type']}.png")

            with open(post_dir / "metadata.json", "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

            print(f"✅ Saved post to: {post_dir}")

    print(f"\n🎉 Jobs run complete! All outputs saved in: {run_dir}")

def main():
    parser = argparse.ArgumentParser(description="unmasked.thoughts Instagram Carousel Generator")
    parser.add_argument("--test", action="store_true", help="Run offline layout test using test_payload.json")
    parser.add_argument("--jobs", action="store_true", help="Run using the JOBS list defined in job_config.py")
    parser.add_argument("-b", "--batch", type=int, default=5, help="Number of carousel posts to generate")
    parser.add_argument("-q", "--questions", type=int, default=4, help="Number of question slides per post")

    args = parser.parse_args()

    if args.test:
        run_test_mode()
    elif args.jobs:
        run_jobs_mode()
    else:
        run_batch_mode(args.batch, args.questions)

if __name__ == "__main__":
    main()
