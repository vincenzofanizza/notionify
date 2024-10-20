import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from langchain_community.utilities import ApifyWrapper
from langchain.output_parsers import PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from notion_client import Client
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class Report(BaseModel):
    title: str = Field(description="A clear and concise title of the report")
    content: str = Field(description="The content of the report")


class ApifyInterface:
    default_run_input = {
        "crawlerType": "playwright:firefox",
        "requestTimeoutSecs": 60,
        "initialConcurrency": 3,
        "maxConcurrency": 10,
        "maxCrawlDepth": 1,
        "maxCrawlPages": 1,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
        },
        "dynamicContentWaitSecs": 5,
    }

    def __init__(self):
        self.client = ApifyWrapper()
        self.database_id = os.environ["NOTION_WEBSITES_DATABASE_ID"]

    def scrape(self, url: str) -> str:
        logger.info(f"Scraping page: {url}")

        trials = [
            {"saveHtmlAsFile": True, "saveMarkdown": False},
            {"saveHtmlAsFile": False, "saveMarkdown": True},
        ]

        while trials:
            try:
                loader = self.client.call_actor(
                    actor_id="apify/website-content-crawler",
                    run_input={
                        **self.default_run_input,
                        "startUrls": [{"url": url}],
                        **trials.pop(),
                    },
                    timeout_secs=180,
                    memory_mbytes=4096,
                    dataset_mapping_function=lambda item: Document(
                        page_content=item.get("markdown", "") or item.get("text", "")
                    ),
                )
                return loader.load()[0].page_content
            except Exception as e:
                logger.error(f"Failed to scrape page. Reason: {e}")

                if not trials:
                    raise e

    def get_favicon(self, url: str) -> str:
        response = requests.get(url)
        try:
            response.raise_for_status()  # Ensure the request was successful
        except requests.exceptions.HTTPError as e:
            logger.error(f"Failed to fetch favicon. Reason: {e}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")
        icon_link = None

        # Look for favicon in the <link> tags
        for rel in ["icon", "shortcut icon"]:
            icon_link = soup.find("link", rel=rel)
            if icon_link:
                break

        # If found, construct the absolute URL of the favicon
        if icon_link and "href" in icon_link.attrs:
            favicon_url = urljoin(url, icon_link["href"])
            logger.info(f"Found favicon: {favicon_url}")
            return favicon_url

        logger.warning("No favicon found")
        return None


class YoutubeInterface:
    def __init__(self):
        self.database_id = os.environ["NOTION_VIDEOS_DATABASE_ID"]

    def _extract_video_id(self, url: str) -> str:
        parsed_url = urlparse(url)
        if parsed_url.hostname == "youtu.be":
            return parsed_url.path[1:]
        if parsed_url.hostname in ("www.youtube.com", "youtube.com"):
            if parsed_url.path == "/watch":
                return parse_qs(parsed_url.query)["v"][0]
            if parsed_url.path.startswith(("/embed/", "/v/")):
                return parsed_url.path.split("/")[2]
        return None

    def _format_transcript(self, transcript: list) -> str:
        return " ".join([entry["text"] for entry in transcript])

    def scrape(self, url: str) -> str:
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "it", "nl"]
        )
        return self._format_transcript(transcript)

    def get_favicon(self, url: str) -> str:
        logger.info(f"Using default favicon for YouTube URL: {url}")
        return "https://img.icons8.com/?size=100&id=19318&format=png&color=000000"

    def get_thumbnail(self, url: str) -> str:
        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL")

        thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"

        # Check if the maxresdefault thumbnail exists
        response = requests.head(thumbnail_url)
        if response.status_code != 200:
            # If not, fall back to the default high-quality thumbnail
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

        logger.info(f"Using thumbnail: {thumbnail_url}")
        return thumbnail_url


class NotionInterface:
    # Regex patterns
    h_re_pattern = r"^#+ "
    numbered_list_re_pattern = r"^\d+\. "
    bulleted_list_re_pattern = r"^[-*] "
    bold_re_pattern = r"\*\*[^*]+\*\*"
    italic_re_pattern = r"\*[^*]+\*"
    link_re_pattern = r"\[.*?\)"

    # Markdown patterns
    h1_pattern = "# "
    h2_pattern = "## "
    h3_pattern = "###"  # NOTE: No trailing space to label h4, h5, and so on as h3.

    CLEANING_PROMPT = PromptTemplate.from_template(
        template="""
        Your task is to improve the formatting of the provided content. Follow these steps:

        1. Remove the main title if it appears on the first line.
        2. Clean markdown formatting:
            - Remove bold formatting from links: "**[link text](https://example.com)**" should be "[link text](https://example.com)".
            - Merge the children list into the parent list item as descriptive text.
        3. Remove any code snippets entirely.
        4. Preserve all other formatting.


        ------------------
        Formatting Guidelines:

        - Only adjust formatting; do not change the text, except for removing the title, nested lists, and code snippets.
        - Provide only the cleaned content without introductory phrases like "Here is the cleaned content."

                        
        ------------------
        Here's an example of the formatting your report should follow:

        ## Overview

        - Y Combinator (YC) offers tactical and fundamental advice to startups, aiming to guide them towards success.
        - The key message is to launch products immediately, gather customer feedback, and iterate, rather than waiting for perfection.
        - This report provides an overview of YC's essential advice for startups, covering topics such as product launch, customer relationships, growth, fundraising, and founder well-being.

        ## Launch and Customer Feedback

        - Launch your product immediately, even if it's mediocre, to understand customers' problems and needs.
        - Do things that don't scale initially to acquire your first customers and figure out their needs.
        - Look for the "90/10 solution": achieve 90% of your goal with 10% of the effort by focusing on solving real customer problems quickly.
        - Talk to your users and gather feedback to improve your product and drive growth.

        ## Customer Relationships and Growth

        - Choose your customers wisely—a small group of customers who love your product is more valuable than a large group with mild interest.
        - Be willing to "fire" customers who are costly or distracting from your main goals.
        - Growth is a result of building a great product that solves customer problems, so focus on product-market fit first.
        - Understand that poor retention and unprofitable products will hinder growth.

        ## Focus and Priorities

        - Do less, but do it well—resist the temptation to chase big deals or spread yourself too thin.
        - Choose one or two key metrics to measure success and base your decisions on their impact.
        - Address the most acute problems your customers have, rather than trying to solve every issue at once.

        ## Fundraising and Valuation

        - Raise money quickly and then focus on improving your company's prospects.
        - Remember that valuation does not equal success—some successful companies raised funds with tiny initial valuations.
        - The money you raise is not your money—spend it with a fiduciary and ethical duty to benefit your company.

        ## Founder Well-being and Relationships

        - Take care of yourself—get enough sleep and exercise, and maintain relationships with friends and family.
        - Foster open and honest communication with your co-founders—strong founder relationships are crucial to success.
        - Be nice—mean people and toxic work environments hinder success.

        ## Conclusion

        YC's advice emphasizes the importance of customer feedback, focused growth, and founder well-being. By launching early, iterating based on customer input, and staying true to their vision, startups can find success. Remember that the road to success is often bumpy, and broken processes or founder disagreements are normal and can be overcome with dedication and open communication.


        ------------------
        Here's the content you need to clean:

        {content}
                        

        ------------------
        Output the cleaned content here, without any additional content like "Here's the cleaned content":
        
        """
    )

    REPORT_PROMPT = PromptTemplate.from_template(
        template="""
        As an expert business researcher, your task is to extract key insights from the provided content. Follow these steps:

        1. Review the content to identify claims, facts, observations, and reference links.
        2. Draft a report that includes all identified information, emphasizing quantitative data for further analysis.
        3. Proofread the draft for omitted details, including news headlines and insights. Iterate until all key points are captured. Include as much detail as possible for a thorough analysis.
        4. Incorporate all external links naturally within the text (in markdown format: [link text](link URL)) without creating a separate list.  
            Example: [YC cohorts grew](https://techcrunch.com/2022/08/02/y-combinator-narrows-current-cohort-size-by-40-citing-downturn-and-funding-environment/) before shrinking in recent years.
        5. Add an introduction and conclusion with appropriate headings.


        ------------------
        Formatting Guidelines:

        - Use neat markdown: headings for sections, bold for emphasis, and lists for structure (choose either bulleted or numbered). 
        - Nested lists are not allowed. Merge the children list into the parent list item as descriptive text.
        - No tables or code snippets are allowed.
        - Include all external links within the report.


        ------------------
        Here's an example of the formatting your report should follow:
        
        ## Overview

        - Y Combinator (YC) offers tactical and fundamental advice to startups, aiming to guide them towards success.
        - The key message is to launch products immediately, gather customer feedback, and iterate, rather than waiting for perfection.
        - This report provides an overview of YC's essential advice for startups, covering topics such as product launch, customer relationships, growth, fundraising, and founder well-being.

        ## Launch and Customer Feedback

        - Launch your product immediately, even if it's mediocre, to understand customers' problems and needs.
        - Do things that don't scale initially to acquire your first customers and figure out their needs.
        - Look for the "90/10 solution": achieve 90% of your goal with 10% of the effort by focusing on solving real customer problems quickly.
        - Talk to your users and gather feedback to improve your product and drive growth.

        ## Customer Relationships and Growth

        - Choose your customers wisely—a small group of customers who love your product is more valuable than a large group with mild interest.
        - Be willing to "fire" customers who are costly or distracting from your main goals.
        - Growth is a result of building a great product that solves customer problems, so focus on product-market fit first.
        - Understand that poor retention and unprofitable products will hinder growth.

        ## Focus and Priorities

        - Do less, but do it well—resist the temptation to chase big deals or spread yourself too thin.
        - Choose one or two key metrics to measure success and base your decisions on their impact.
        - Address the most acute problems your customers have, rather than trying to solve every issue at once.

        ## Fundraising and Valuation

        - Raise money quickly and then focus on improving your company's prospects.
        - Remember that valuation does not equal success—some successful companies raised funds with tiny initial valuations.
        - The money you raise is not your money—spend it with a fiduciary and ethical duty to benefit your company.

        ## Founder Well-being and Relationships

        - Take care of yourself—get enough sleep and exercise, and maintain relationships with friends and family.
        - Foster open and honest communication with your co-founders—strong founder relationships are crucial to success.
        - Be nice—mean people and toxic work environments hinder success.

        ## Conclusion

        YC's advice emphasizes the importance of customer feedback, focused growth, and founder well-being. By launching early, iterating based on customer input, and staying true to their vision, startups can find success. Remember that the road to success is often bumpy, and broken processes or founder disagreements are normal and can be overcome with dedication and open communication.
                                                  

        ------------------
        Here's the content you need to generate the report:

        {content}
                        
        
        ------------------                        
        {format_instructions}

       
        ------------------
        Output your generated report here, without any additional content like "Here's the report". Don't add a main title:
        
        """
    )

    def __init__(self, database_id: str):
        self.client = Client(auth=os.environ["NOTION_TOKEN"])
        self.database_id = database_id

    def __identify_block_type(self, text: str) -> str:
        if text.startswith(self.h3_pattern):
            return "heading_3"
        if text.startswith(self.h2_pattern):
            return "heading_2"
        if text.startswith(self.h1_pattern):
            return "heading_1"
        if re.match(self.numbered_list_re_pattern, text):
            return "numbered_list_item"
        if re.match(self.bulleted_list_re_pattern, text):
            return "bulleted_list_item"
        return "paragraph"

    def __clean_content(self, content: str) -> str:
        logger.info("Cleaning content")

        # Create cleaning chain
        llm = ChatGroq(model="llama3-70b-8192", temperature=0)
        chain = self.CLEANING_PROMPT | llm

        result = chain.invoke({"content": content}).content

        logger.info(f"Cleaned content: {result}")
        return result

    def __create_block(self, text: str, block_type: str) -> dict:
        if block_type.startswith("heading"):
            text = re.sub(self.h_re_pattern, "", text)
        if block_type == "numbered_list_item":
            text = re.sub(self.numbered_list_re_pattern, "", text)
        if block_type == "bulleted_list_item":
            text = re.sub(self.bulleted_list_re_pattern, "", text)

        # Split text into bold, italic, and links
        combined_pattern = (
            f"({self.bold_re_pattern}|{self.italic_re_pattern}|{self.link_re_pattern})"
        )
        split_text = [part for part in re.split(combined_pattern, text) if part]

        # Create rich text
        rich_text = []
        for part in split_text:
            if not part:
                continue

            logger.info(f"Assigning rich text ({block_type}): {part}")
            if part.startswith("**"):
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": part.replace("**", "")},
                        "annotations": {"bold": True},
                    }
                )
            elif part.startswith("*"):
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": part.replace("*", "")},
                        "annotations": {"italic": True},
                    }
                )
            elif part.startswith("["):
                link_text, link_url = part[1:-1].split("](")
                rich_text.append(
                    {
                        "type": "text",
                        "text": {"content": link_text, "link": {"url": link_url}},
                    }
                )
            else:
                rich_text.append({"type": "text", "text": {"content": part}})

        return {
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": rich_text},
        }

    def generate_report(self, content: str) -> Report:
        logger.info("Generating report")

        # Create report chain
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        parser = PydanticOutputParser(pydantic_object=Report)
        chain = self.REPORT_PROMPT | llm | parser

        result = chain.invoke(
            {
                "content": content,
                "format_instructions": parser.get_format_instructions(),
            }
        )

        logger.info(f"Generated report: {result}")
        return result

    def create_page(
        self,
        url: str,
        report: Report,
        icon: str | None = None,
        cover: str | None = None,
    ) -> dict:
        report.content = self.__clean_content(report.content)

        # Split content by paragraphs and create blocks
        children_blocks = []
        for block in report.content.split("\n"):
            block = block.strip()
            if not block:
                continue

            block_type = self.__identify_block_type(block)
            children_blocks.append(self.__create_block(block, block_type))

        # Create new page
        kwargs = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": report.title}}]},
                "URL": {"url": url},
            },
            "children": children_blocks,
        }

        if icon:
            kwargs["icon"] = {"type": "external", "external": {"url": icon}}

        if cover:
            kwargs["cover"] = {"type": "external", "external": {"url": cover}}

        page = self.client.pages.create(**kwargs)

        logger.info(f"Created new page: {page['url']}")
        return page
