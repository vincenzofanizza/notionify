import os
import re
import logging
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from langchain_community.utilities import ApifyWrapper
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain_cohere import ChatCohere
from langchain_groq import ChatGroq
from notion_client import Client

from textwrap import dedent
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class ApifyInterface:
    def __init__(self):
        self.client = ApifyWrapper()

    def scrape_page(self, url: str) -> str:
        logger.info(f"Scraping page: {url}")
        loader = self.client.call_actor(
            actor_id="apify/website-content-crawler",
            run_input={
                "startUrls": [{"url": url}],
                "saveHtmlAsFile": True,
                "saveMarkdown": False,
                "requestTimeoutSecs": 120,
                "initialConcurrency": 3,
                "maxConcurrency": 10,
                "maxCrawlDepth": 1,
                "maxCrawlPages": 1,
                "dynamicContentWaitSecs": 5
            },
            timeout_secs=180,
            memory_mbytes=8192,
            dataset_mapping_function=lambda item: Document(page_content=item.get("text", "")))
        return loader.load()[0].page_content

class NotionInterface:
    h_re_pattern = r"^#+ "
    h1_pattern = "# "
    h2_pattern = "## "
    h3_pattern = "###"  # NOTE: No trailing space to label h4, h5, and so on as h3.
    numbered_list_re_pattern = r"^\d+\. "
    bulleted_list_re_pattern = r"^[-*] "
    bold_re_pattern = r"\*\*[^*]+\*\*"
    italic_re_pattern = r"\*[^*]+\*"
    link_re_pattern = r"\[.*?\)"

    TITLE_PROMPT = PromptTemplate.from_template(
        template=dedent("""
        As an expert business researcher, your task is to assign a title to the given content. Follow these steps:
        1. Carefully read the report.
        2. Assign a clear and concise title to the report.
        3. Your response should consist of only the title in plain text. Do not add extra formatting like headings or bold/italic text.
        
                        
        ------------------
        CONTENT:

        {content}
                        

        ------------------
        TITLE:"""))
    
    CLEANING_PROMPT = PromptTemplate.from_template(
        template=dedent("""
        Clean the markdown formatting of the given content:
        - Remove the main title from the first line, if present.
        - Leave any formatting intact, like headings, bold/italic text, and lists.
        - Only provide the cleaned content in your response. Do not start with phrases like "Here is the cleaned content:".
        
                        
        ------------------
        CONTENT:

        {content}
                        

        ------------------
        CLEANED CONTENT:"""))
                        
    SUMMARY_PROMPT = PromptTemplate.from_template(
        template=dedent("""
        As an expert business researcher, your task is to extract the most important insights from the given content. Follow these steps:
        1. Carefully look at the content and identify any claim, fact, or observation.
        2. Write a draft of the report including all information identified in step 1. Report as much quantitative data as possible, as they can be used for further analysis.
        3. Proofread your draft and look for information you omitted. Iterate over it until all key information are included in the report.
        4. Add in-line links for further reading.
        5. Complete the summary by adding an introduction and a conclusion.
                        
        NOTE:
        - Format your response in neat markdown. Use headings for paragraphs, bold to highlight text, lists for structured content and in-line links.
        - Do not include tables.
        - When structuring your response, **only use one type of list: either numbered or bulleted**.
        - Your response should only include the summary. Do not start with "Here is a summary of the key insights from the content provided".

                                                    
        ------------------
        CONTENT:

        {content}

                        
        ------------------
        SUMMARY:"""))


    def __init__(self):
        self.client = Client(auth=os.environ["NOTION_TOKEN"])
    
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
    
    def __assign_title(self, content: str) -> str:
        logger.info("Assigning title")
        prompt_value = self.TITLE_PROMPT.invoke({"content": content})

        llm = ChatGroq(model="llama3-70b-8192")
        result = llm.invoke(prompt_value).content

        logger.info(f"Title: {result}")
        return result.replace("\"", "")
    
    def __clean_content(self, content: str) -> str:
        logger.info("Cleaning content")
        prompt_value = self.CLEANING_PROMPT.invoke({"content": content})

        llm = ChatGroq(model="llama3-70b-8192")
        result = llm.invoke(prompt_value).content
        return result

    def __create_block(self, text: str, block_type: str) -> dict:
        if block_type.startswith("heading"):
            text = re.sub(self.h_re_pattern, "", text)
        if block_type == "numbered_list_item":
            text = re.sub(self.numbered_list_re_pattern, "", text)
        if block_type == "bulleted_list_item":
            text = re.sub(self.bulleted_list_re_pattern, "", text)

        # Split text into bold, italic, and links
        combined_pattern = f"({self.bold_re_pattern}|{self.italic_re_pattern}|{self.link_re_pattern})"
        split_text = [part for part in re.split(combined_pattern, text) if part]

        # Create rich text
        rich_text = []
        for part in split_text:
            if not part: continue

            logger.info(f"Assigning rich text ({block_type}): {part}")
            if part.startswith("**"):
                rich_text.append({"type": "text", "text": {"content": part.replace("**", "")}, "annotations": {"bold": True}})
            elif part.startswith("*"):
                rich_text.append({"type": "text", "text": {"content": part.replace("*", "")}, "annotations": {"italic": True}})
            elif part.startswith("["):
                link_text, link_url = part[1:-1].split("](")
                rich_text.append({"type": "text", "text": {"content": link_text, "link": {"url": link_url}}})
            else:
                rich_text.append({"type": "text", "text": {"content": part}})
        
        return {
            "object": "block",
            "type": block_type,
            block_type: {
                "rich_text": rich_text
            }
        }
    
    def summarize_content(self, content: str) -> str:
        logger.info("summarizing content")
        prompt_value = self.SUMMARY_PROMPT.invoke({"content": content})

        llm = ChatCohere(model="command-r-plus")
        result = llm.invoke(prompt_value).content

        logger.info(f"Summarized content: {result}")
        return result

    def create_page(self, url: str, content: str, icon: str | None = None) -> dict:
        title = self.__assign_title(content)
        cleaned_content = self.__clean_content(content)
        
        # Split content by paragraphs and create blocks
        children_blocks = []
        for block in cleaned_content.split("\n"):
            block = block.strip()        
            if not block: continue

            block_type = self.__identify_block_type(block)
            children_blocks.append(self.__create_block(block, block_type))
        
        # Create new page
        kwargs = {
            "parent": {
                "database_id": os.environ["NOTION_DATABASE_ID"]
            },
            "properties": {
                "Name": {"title": [{"text": {"content": title}}]},
                "URL": {"url": url}
            },
            "children": children_blocks
        }

        if icon:
            kwargs["icon"] = {"type": "external", "external": {"url": icon}}

        page = self.client.pages.create(**kwargs)

        logger.info(f"Created new page: {page['url']}")
        return page


def find_favicon(url: str) -> str:
    response = requests.get(url)
    try:
        response.raise_for_status()  # Ensure the request was successful
    except requests.exceptions.HTTPError as e:
        logger.error(f"Failed to fetch favicon. Reason: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    icon_link = None

    # Look for favicon in the <link> tags
    for rel in ['icon', 'shortcut icon']:
        icon_link = soup.find('link', rel=rel)
        if icon_link:
            break

    # If found, construct the absolute URL of the favicon
    if icon_link and 'href' in icon_link.attrs:
        favicon_url = urljoin(url, icon_link['href'])
        logger.info(f"Found favicon: {favicon_url}")
        return favicon_url
    
    logger.warning("No favicon found")
    return None
