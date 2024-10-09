# WebDigest for Notion

## Overview

WebDigest for Notion is a Chrome extension that provides an easy way to summarize web pages and save the summaries to Notion. It uses a combination of web scraping, natural language processing, and the Notion API to create concise reports from any web page or YouTube video.

## Features

- Summarize any web page or YouTube video with a single click
- Automatically scrape content using Apify for websites or YouTube transcripts for videos
- Generate comprehensive reports using advanced language models using 4o-mini and llama3-70b
- Save summaries directly to your Notion database
- Customizable Notion integration with separate databases for websites and videos
- Automatic favicon and thumbnail extraction for rich visual representation in Notion

## Technical Stack

- **Backend**: Firebase Functions (Python)
- **APIs and Services**:
  - Apify for web scraping
  - YouTube Transcript API for video transcripts
  - OpenAI 4o-mini and Groq for text generation
  - Notion API for saving summaries
- **Chrome Extension**: JavaScript

## Setup and Installation

1. Clone this repository
2. Set up a Firebase project and install the Firebase CLI
3. Configure your environment variables:
   - Copy `functions/.env.sample` to `functions/.env`
   - Fill in all required API keys and IDs
4. Install dependencies:
   ```
   cd functions
   pip install -r requirements.txt
   ```
5. Deploy the Firebase Function:
   ```
   firebase deploy --only functions
   ```
6. Load the Chrome extension (frontend code not provided in this repository)

## Configuration

Ensure you have set up the following in your `functions/.env` file:

```
# Notion
NOTION_TOKEN=your_notion_integration_token
NOTION_WEBSITES_DATABASE_ID=your_notion_websites_database_id
NOTION_VIDEOS_DATABASE_ID=your_notion_videos_database_id

# Apify
APIFY_API_TOKEN=your_apify_api_token

# API Keys
OPENAI_API_KEY=your_openai_api_key
GROQ_API_KEY=your_groq_api_key

# Chrome extension
CHROME_EXTENSION_ID=your_chrome_extension_id
```

Replace the placeholder values with your actual API keys and IDs.

## Usage

1. Install the Chrome extension (frontend not provided in this repository)
2. Navigate to any web page or YouTube video you want to summarize
3. Click the extension icon to trigger the summarization process
4. Wait for the process to complete (this may take a few moments depending on the content length)
5. The summary will be automatically saved to your configured Notion database

## Firebase Function

The main Firebase Function (`create_page`) handles the summarization process:

1. Receives a URL from the Chrome extension
2. Determines if it's a website or YouTube video
3. Scrapes the content using the appropriate method
4. Generates a report using advanced language models
5. Cleans and formats the content
6. Saves the summary to the appropriate Notion database

## Customization

You can customize various aspects of the summarization process:

- Adjust the Apify scraping parameters in `ApifyInterface`
- Modify the report generation prompt in `NotionInterface.REPORT_PROMPT`
- Change the content cleaning prompt in `NotionInterface.CLEANING_PROMPT`
- Customize the Notion page structure in `NotionInterface.create_page`

## Limitations

- The current implementation has a timeout of 540 seconds (9 minutes) for the Firebase Function
- There's a maximum of 2 instances allowed for the function
- The function uses 2GB of memory
