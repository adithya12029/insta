import os
import time
import shutil
from pathlib import Path
import requests
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from PIL import Image

load_dotenv()

# ==========================================
# CONFIGURATION & CREDENTIALS
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

# Local folder to archive posts after successful upload
APPROVED_ARCHIVE_DIR = os.getenv("APPROVED_ARCHIVE_DIR", str(BASE_DIR / "carousels" / "approved"))
POST_TARGET_FOLDER = os.getenv("POST_TARGET_FOLDER", "")

# Cloudinary Credentials (https://cloudinary.com)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# Instagram Graph API Credentials (Meta Developer Portal)
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

# Configure Cloudinary SDK
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)


# ==========================================
# POSTING & UPLOAD FUNCTIONS
# ==========================================

def upload_folder_images_to_cloud(folder_path):
    """Scans images, converts them to clean JPEGs to satisfy Instagram, uploads to Cloudinary, and returns public URLs."""
    valid_extensions = ('.png', '.jpg', '.jpeg')
    image_files = sorted([
        f for f in os.listdir(folder_path) 
        if f.lower().endswith(valid_extensions)
    ])

    if len(image_files) < 2 or len(image_files) > 10:
        raise ValueError(f"Instagram requires between 2 and 10 images for a carousel. Found {len(image_files)}.")

    print(f"   [CLOUDINARY] Processing and uploading {len(image_files)} slide images as JPEGs...")
    public_urls = []
    
    for filename in image_files:
        file_path = os.path.join(folder_path, filename)
        
        # Open image and convert to RGB JPEG (flattens transparency to white background)
        img = Image.open(file_path)
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = background
        else:
            img = img.convert("RGB")
        
        # Save temporary converted JPEG version locally
        temp_jpg_path = file_path.rsplit('.', 1)[0] + '_temp.jpg'
        img.save(temp_jpg_path, 'JPEG', quality=95)
        
        try:
            response = cloudinary.uploader.upload(temp_jpg_path)
            url = response.get("secure_url")
            public_urls.append(url)
            print(f"      └─ Uploaded: {filename} -> JPEG")
        finally:
            # Cleanup temporary file
            if os.path.exists(temp_jpg_path):
                os.remove(temp_jpg_path)
     
    return public_urls


def publish_instagram_carousel(image_urls, caption=""):
    """Publishes a list of image URLs to Instagram via Meta Graph API."""
    base_url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media"
    
    # Step 1: Create item containers for each image
    print("   [INSTAGRAM] Creating item containers...")
    container_ids = []
    for url in image_urls:
        res = requests.post(base_url, data={
            "image_url": url,
            "is_carousel_item": "true",
            "access_token": ACCESS_TOKEN
        }).json()
        
        if "id" not in res:
            raise Exception(f"Container creation failed: {res}")
        container_ids.append(res["id"])

    # Step 2: Create main Carousel container
    print("   [INSTAGRAM] Creating main Carousel container...")
    carousel_res = requests.post(base_url, data={
        "media_type": "CAROUSEL",
        "children": ",".join(container_ids),
        "caption": caption,
        "access_token": ACCESS_TOKEN
    }).json()
    
    if "id" not in carousel_res:
        raise Exception(f"Carousel container creation failed: {carousel_res}")
        
    carousel_id = carousel_res["id"]
    time.sleep(5)  # Pause to allow Meta servers to process media assets

    # Step 3: Publish Carousel
    print("   [INSTAGRAM] Publishing post...")
    publish_res = requests.post(
        f"https://graph.facebook.com/v19.0/{INSTAGRAM_ACCOUNT_ID}/media_publish",
        data={"creation_id": carousel_id, "access_token": ACCESS_TOKEN}
    ).json()

    if "id" in publish_res:
        return publish_res["id"]
    else:
        raise Exception(f"Publish failed: {publish_res}")


def resolve_target_folder():
    """Return the first valid carousel folder from env or the latest generated batch."""
    if POST_TARGET_FOLDER and os.path.exists(POST_TARGET_FOLDER):
        return POST_TARGET_FOLDER

    carousels_root = BASE_DIR / "carousels"
    if not carousels_root.exists():
        return POST_TARGET_FOLDER

    candidates = []
    for folder in sorted(carousels_root.iterdir(), key=lambda p: p.name.lower()):
        if not folder.is_dir():
            continue
        for child in sorted(folder.iterdir(), key=lambda p: p.name.lower()):
            if child.is_dir() and any(file.name.lower().endswith((".png", ".jpg", ".jpeg")) for file in child.iterdir() if file.is_file()):
                candidates.append(str(child))

    if candidates:
        return candidates[-1]

    return POST_TARGET_FOLDER


def process_folder_path(folder_path):
    """Pipeline: Takes a direct folder path, uploads slides, posts to Instagram, and archives it."""
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder path does not exist: {folder_path}")
        return

    folder_name = os.path.basename(folder_path)
    print(f"\n[PROCESSING] -> Target Folder: {folder_name}")

    try:
        # 1. Upload slides to Cloudinary
        image_urls = upload_folder_images_to_cloud(folder_path)

        # 2. Build caption
        clean_tag = folder_name.replace(" ", "_").lower()
        caption = f"Check out this latest breakdown! 🚀\n\n#{clean_tag} #carousel #automation"

        # 3. Post to Instagram
        post_id = publish_instagram_carousel(image_urls, caption=caption)
        print(f"   [SUCCESS] Live on profile! (Post ID: {post_id})")

        # 4. Move folder to archive
        os.makedirs(APPROVED_ARCHIVE_DIR, exist_ok=True)
        dest_path = os.path.join(APPROVED_ARCHIVE_DIR, folder_name)
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.move(folder_path, dest_path)
        print(f"   [ARCHIVED] Moved local folder -> {dest_path}")

    except Exception as e:
        print(f"   [ERROR] Failed to process '{folder_name}': {e}")


if __name__ == "__main__":
    TARGET_FOLDER_TO_POST = resolve_target_folder()
    if not TARGET_FOLDER_TO_POST:
        raise FileNotFoundError("No valid carousel folder found. Set POST_TARGET_FOLDER in .env or generate a carousel first.")

    process_folder_path(TARGET_FOLDER_TO_POST)
