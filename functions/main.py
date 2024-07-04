import os
import logging

from firebase_functions import https_fn, options
from firebase_admin import initialize_app
from dotenv import load_dotenv

from utils import ApifyInterface, NotionInterface, find_favicon
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
    ))
def create_page(req: https_fn.Request) -> https_fn.Response:
    url = req.args.get("url")
    if not url:
        return https_fn.Response(status=400, response="Missing 'url' parameter")

    try:
        logger.info(f"Creating new page for {url}")
        setup_logger()

        apify = ApifyInterface()
        notion = NotionInterface()

        # Scrape content
        page_content = apify.scrape_page(url)

        # Find favicon
        icon = find_favicon(url)

        # Summarize content
        summary = notion.summarize_content(page_content)

        # Create new page
        page = notion.create_page(url, summary, icon)

        return https_fn.Response(status=200, response=page["url"])
    except Exception as e:
        logger.error(e)
        return https_fn.Response(status=500, response=str(e))
