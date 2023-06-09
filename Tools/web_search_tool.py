import Agents.worker_agent as agent
import openai
import re
import requests
from bs4 import BeautifulSoup
from Constants import settings
from serpapi import GoogleSearch
import logging

logging.basicConfig(filename='web_search_log.txt', level=1)


def web_search_tool(query: str):
    query = format_query(query)
    search_params = {
        "engine": "google",
        "q": query,
        "api_key": settings.SERPAPI_KEY,
        "num": 5  # edit this up or down for more results, though higher often results in OpenAI rate limits
    }
    search_results = GoogleSearch(search_params)
    search_results = search_results.get_dict()
    try:
        search_results = search_results["organic_results"]
    except Exception as err:
        search_results = {}
    search_results = simplify_search_results(search_results)
    print("\033[90m\033[3m" + "Completed search. Now scraping results.\n" + "\033[0m")
    results = ""
    # Loop through the search results
    for result in search_results:
        # Extract the URL from the result
        url = result.get('link')
        # Call the web_scrape_tool function with the URL
        print("\033[90m\033[3m" + "Scraping: " + url + "" + "...\033[0m")
        content = web_scrape_tool(url, query)
        print("\033[90m\033[3m" + str(content[0:100])[0:100] + "...\n" + "\033[0m")
        results += str(content) + ". "

    return results


def simplify_search_results(search_results):
    simplified_results = []
    for result in search_results:
        simplified_result = {
            "position": result.get("position"),
            "title": result.get("title"),
            "link": result.get("link"),
            "snippet": result.get("snippet")
        }
        simplified_results.append(simplified_result)
    return simplified_results


def web_scrape_tool(url: str, task: str):
    content = fetch_url_content(url)
    if content is None:
        return None

    text = extract_text(content)
    print("\033[90m\033[3m" + "Scrape completed. Length:" + str(
        len(text)) + ".Now extracting relevant info..." + "...\033[0m")
    info = extract_relevant_info(agent.get_objective(), text[0:5000], task)
    links = extract_links(content)

    result = f"{info} URLs: {', '.join(links)}"

    return result


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
}


def fetch_url_content(url: str):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching the URL: {e}")
        return ""


def extract_links(content: str):
    soup = BeautifulSoup(content, "html.parser")
    links = [link.get('href') for link in soup.findAll('a', attrs={'href': re.compile("^https?://")})]
    return links


def extract_text(content: str):
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(strip=True)
    return text


def extract_relevant_info(objective, large_string, task):
    chunk_size = 3000
    overlap = 500
    notes = ""

    for i in range(0, len(large_string), chunk_size - overlap):
        chunk = large_string[i:i + chunk_size]

        messages = [
            {"role": "system", "content": f"Objective: {objective}\nCurrent Task:{task}"},
            {"role": "user",
             "content": f"Analyze the following text and extract information relevant to our objective and current task, and only information relevant to our objective and current task. If there is no relevant information do not say that there is no relevant information related to our objective. ### Then, update or start our notes provided here (keep blank if currently blank): {notes}.### Text to analyze: {chunk}.### Updated Notes:"}
        ]
        # todo replace with better api call
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,
            n=1,
            stop="###",
            temperature=0.7,
        )

        notes += response.choices[0].message['content'].strip() + ". "

    return notes


def format_query(query: str) -> str:
    return query
