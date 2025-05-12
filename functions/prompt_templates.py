report_prompt_template = """
# Goal
As an expert researcher, your task is to make a report of key insights extracted from the provided content. Follow these steps:
1. Review the content to identify claims, facts, observations, and reference links. Focus on the following information:
    - Specific and actionable insights, such as details about new technologies, financial markets, or business strategies.
    - Quantitative data of any kind: statistics, reports, trends, etc.
    - Informative and educational content, such as advice for personal and professional growth.
2. Draft a report that includes all identified information, emphasizing quantitative data for further analysis.
3. Proofread the draft for omitted details, including news headlines and insights. Iterate until all key points are captured. Include as much detail as possible for a thorough analysis.
4. Incorporate all external links naturally within the text (in markdown format: [link text](link URL)) without creating a separate list.  
    Example: [YC cohorts grew](https://techcrunch.com/2022/08/02/y-combinator-narrows-current-cohort-size-by-40-citing-downturn-and-funding-environment/) before shrinking in recent years.
5. Add an introduction and conclusion with appropriate headings.

# User Guidance
The user has provided the following guidance for this report. Please focus your report accordingly:

{guidance}

# Format instructions

## Allowed markdown elements
- Headings 2 and 3 for sections
- Bold (**text**) and italic (*text*) for emphasis
- Lists for structure (choose either bulleted or numbered)
- Do not use square brackets ([]) unless it's a link (e.g. [link text](link URL))
- Do not use other markdown elements like tables or code snippets

## Minimize indentations
- Having lists is allowed, but nested lists make the content harder to read. If nested lists are present, merge the children list into the parent item as plain text.

Example 1:
- Elon Musk is the CEO of the following companies:
    - Tesla
    - SpaceX
    - Neuralink
Should be:
- Elon Musk is the CEO of the following companies: Tesla, SpaceX, and Neuralink.

Example 2:
- The 2018-19 U.S.-China trade war resulted in:
    - 133% decline in the Chinese Yuan
    - 13% devaluation of major currencies against the U.S. dollar
    - Maximum drawdown of 20% in the S&P 500
Should be:
- The 2018-19 U.S.-China trade war resulted in a 133% decline in the Chinese Yuan, a 13% devaluation of major currencies against the U.S. dollar, and a maximum drawdown of 20% in the S&P 500.

## External links
Include all external links within the report.

{format_instructions}


# Example
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


# Content
Here's the content you need to generate the report:
{content}

# Output
Output your generated report here, without any additional content like "Here's the report". Don't add a main title:
"""
