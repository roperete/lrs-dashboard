"""
Web scraping for simulant information from supplier sites and databases
"""
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time


class WebScraper:
    """Scrape simulant information from websites"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def search_google(self, query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search Google for simulant information
        Note: For production, consider using official Google Search API
        """
        results = []

        # Simple DuckDuckGo search (no API key needed)
        try:
            url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                result_divs = soup.find_all('div', class_='result')

                for div in result_divs[:num_results]:
                    title_elem = div.find('a', class_='result__a')
                    snippet_elem = div.find('a', class_='result__snippet')

                    if title_elem and snippet_elem:
                        results.append({
                            "title": title_elem.text.strip(),
                            "url": title_elem.get('href', ''),
                            "snippet": snippet_elem.text.strip(),
                            "source_type": "web_search"
                        })

            time.sleep(1)  # Be respectful

        except Exception as e:
            print(f"⚠️  Web search failed: {e}")

        return results

    def scrape_url(self, url: str) -> Optional[Dict[str, str]]:
        """Scrape text content from a specific URL"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            return {
                "source": f"Website: {url}",
                "url": url,
                "text": text[:10000],  # Limit to 10k chars
                "source_type": "web_scrape"
            }

        except Exception as e:
            print(f"⚠️  Failed to scrape {url}: {e}")
            return None

    def search_for_simulant(self, simulant_name: str) -> List[Dict[str, str]]:
        """Search web for information about a specific simulant"""
        results = []

        # Search query
        query = f'"{simulant_name}" lunar regolith simulant'
        print(f"   🔍 Searching web for: {query}")

        # Get search results
        search_results = self.search_google(query, num_results=3)

        # Scrape top results
        for result in search_results:
            url = result.get('url')
            if url and url.startswith('http'):
                scraped = self.scrape_url(url)
                if scraped:
                    scraped['search_snippet'] = result.get('snippet', '')
                    results.append(scraped)
                time.sleep(2)  # Be respectful

        print(f"   Found {len(results)} web pages")
        return results

    def scrape_supplier_site(self, supplier_url: str, simulant_name: str) -> Optional[Dict[str, str]]:
        """Scrape specific supplier site for simulant info"""
        # Search supplier site
        search_url = f"{supplier_url}?s={simulant_name}"

        scraped = self.scrape_url(search_url)
        if scraped:
            scraped['source'] = f"Supplier: {supplier_url}"

        return scraped


if __name__ == "__main__":
    # Test
    scraper = WebScraper()
    results = scraper.search_for_simulant("JSC-1A")
    print(f"Found {len(results)} web results")
