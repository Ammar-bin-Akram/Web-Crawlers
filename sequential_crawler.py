import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

class SequentialWebCrawler:
    def __init__(self, seed_url, max_pages=5):
        self.seed_url = seed_url
        self.max_pages = max_pages
        self.visited_urls = set()
        self.domain = urlparse(seed_url).netloc
        self.results = []
        
    def is_valid_url(self, url):
        """Check if URL belongs to the same domain and is not already visited"""
        parsed = urlparse(url)
        return parsed.netloc == self.domain and url not in self.visited_urls
    
    def fetch_page(self, url):
        """Fetch the page content"""
        try:
            headers = {'User-Agent': 'SequentialWebCrawler/1.0'}
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_links_and_title(self, html, base_url):
        """Extract all links and the page title from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title = soup.title.string if soup.title else "No Title"
        
        # Extract all valid links
        links = set()
        for link in soup.find_all('a', href=True):
            absolute_url = urljoin(base_url, link['href'])
            if self.is_valid_url(absolute_url):
                links.add(absolute_url)
        
        return title, links
    
    def crawl(self):
        """Main crawl method that processes pages sequentially"""
        queue = [self.seed_url]
        start_time = time.time()
        
        while queue and len(self.visited_urls) < self.max_pages:
            current_url = queue.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"Crawling: {current_url}")
            self.visited_urls.add(current_url)
            
            html = self.fetch_page(current_url)
            if not html:
                continue
                
            title, links = self.extract_links_and_title(html, current_url)
            self.results.append({
                'url': current_url,
                'title': title,
                'links': list(links)
            })
            
            # Add new links to queue
            for link in links:
                if link not in self.visited_urls and link not in queue:
                    queue.append(link)
        
        elapsed_time = time.time() - start_time
        print(f"\nCrawled {len(self.visited_urls)} pages in {elapsed_time:.2f} seconds")
        return self.results, elapsed_time

# Example usage
if __name__ == "__main__":
    seed_url = "https://en.wikipedia.org/wiki/Main_Page"  # Replace with your seed URL
    crawler = SequentialWebCrawler(seed_url, max_pages=50)
    results, total_time = crawler.crawl()
    
    # Print results
    print("\nCrawl Results:")
    for i, page in enumerate(results, 1):
        print(f"{i}. {page['title']} - {page['url']}")
    with open('crawl_results.txt', 'a') as f:
        f.write(f'Crawl Results: \n')
        f.write(f'Total time taken: {total_time:.2f} seconds\n')
