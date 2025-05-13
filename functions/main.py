import os
import logging
from urllib.parse import urlparse
from firebase_functions import https_fn, options
from firebase_admin import initialize_app
from dotenv import load_dotenv

from utils import (
    NotionInterface,
    scrape_website_with_apify,
    scrape_youtube_with_apify,
    scrape_youtube_with_transcript,
)
from logger import setup_logger

logger = logging.getLogger(__name__)

load_dotenv()

initialize_app()


@https_fn.on_request(
    region="europe-west1",
    max_instances=2,
    timeout_sec=540,
    memory=options.MemoryOption.GB_2,
    cors=options.CorsOptions(
        cors_origins=[f"chrome-extension://{os.environ['CHROME_EXTENSION_ID']}"],
        cors_methods=["get", "post"],
    ),
)
def create_notion_page(req: https_fn.Request) -> https_fn.Response:
    url = req.args.get("url")
    if not url:
        return https_fn.Response(status=400, response="Missing 'url' parameter")

    guidance = req.args.get("guidance", "")

    try:
        logger.info(f"Creating new page for {url}")
        setup_logger()

        is_youtube = urlparse(url).netloc in ["www.youtube.com", "youtu.be"]
        if is_youtube:
            try:
                result = scrape_youtube_with_apify(url)
            except Exception as e:
                result = scrape_youtube_with_transcript(url)

        else:
            result = scrape_website_with_apify(url)

        notion = NotionInterface(is_youtube=is_youtube)
        report = notion.generate_report(result["content"], guidance)
        page = notion.create_page(url, report, result["icon"], result["cover"])

        return https_fn.Response(status=200, response=page["url"])
    except Exception as e:
        logger.error(e)
        return https_fn.Response(status=500, response=str(e))
