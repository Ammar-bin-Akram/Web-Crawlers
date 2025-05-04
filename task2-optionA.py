import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from queue import Queue
import threading
import time
from tqdm import tqdm
import matplotlib.pyplot as plt

# Configuration
NUM_THREADS = 4
MAX_URLS = 50
DOMAIN_LIMIT = None

# Shared resources
visited = set()
url_queue = Queue()
visited_lock = threading.Lock()
progress_bar = None
stop_crawling = False
worker_stats = {}
queue_sizes = []
timestamps = []

def is_valid_url(url):
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def crawl_url(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else "No Title"
        print(f"[{threading.current_thread().name}] Crawled: {url} - Title: {title}")
        links = soup.find_all('a', href=True)
        return [urljoin(url, link['href']) for link in links]
    except Exception as e:
        print(f"[{threading.current_thread().name}] Error fetching {url}: {e}")
        return []

def worker():
    global progress_bar, stop_crawling
    name = threading.current_thread().name
    worker_stats[name] = 0
    while True:
        try:
            url = url_queue.get(timeout=2)
        except:
            break  # Timeout reached — exit if queue is empty

        with visited_lock:
            if stop_crawling or url in visited or (DOMAIN_LIMIT and DOMAIN_LIMIT not in url):
                url_queue.task_done()
                continue
            visited.add(url)
            worker_stats[name] += 1
            if len(visited) >= MAX_URLS:
                stop_crawling = True
            if progress_bar:
                progress_bar.update(1)

        for link in crawl_url(url):
            if stop_crawling:
                break
            if is_valid_url(link):
                with visited_lock:
                    if not stop_crawling and link not in visited:
                        url_queue.put(link)

        url_queue.task_done()

def monitor_queue():
    while not stop_crawling:
        with visited_lock:
            queue_sizes.append(url_queue.qsize())
            timestamps.append(time.time())
        time.sleep(1)


def crawl_parallel(seed_url):
    global progress_bar
    url_queue.put(seed_url)
    threads = []

    progress_bar = tqdm(total=MAX_URLS, desc="Crawling Progress")
    start_time = time.time()

    # Start worker threads
    for i in range(NUM_THREADS):
        t = threading.Thread(target=worker, name=f"Worker-{i+1}")
        t.start()
        threads.append(t)

    # Start monitor thread
    monitor = threading.Thread(target=monitor_queue)
    monitor.start()

    # Wait for crawling
    url_queue.join()

    for _ in threads:
        url_queue.put(None)
    for t in threads:
        t.join()

    monitor.join()
    progress_bar.close()
    end_time = time.time()

    elapsed_time = end_time - start_time
    print(f"\n Crawled {len(visited)} pages in {elapsed_time:.2f} seconds.")
    print(f" Avg speed: {len(visited)/elapsed_time:.2f} pages/sec")
    print(f'Total pages crawled: {len(visited)}')
    print(f'Time taken: {elapsed_time:.2f} seconds')
    # writing the stats to a file
    with open('crawl_results.txt', 'a') as f:
        f.write(f'Crawl results using multithreading:\n')
        f.write(f'Number of threads: {NUM_THREADS}\n')
        f.write(f'Total time elapsed: {elapsed_time:.2f} seconds\n')


if __name__ == "__main__":
    print(f'Using {NUM_THREADS} threads for crawling')
    seed = "https://www.youtube.com"
    DOMAIN_LIMIT = urlparse(seed).netloc
    crawl_parallel(seed)
