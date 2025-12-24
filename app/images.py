from dotenv import load_dotenv
from imagekitio import AsyncImageKit
import os

load_dotenv()
imagekit = AsyncImageKit(
    private_key=os.environ.get("IMAGEKIT_PRIVATE_KEY")
)
URL_ENDPOINT = os.environ.get("IMAGEKIT_URL")

