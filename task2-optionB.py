from mpi4py import MPI
import requests
from bs4 import BeautifulSoup
import time
import sys

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
MAX_PAGES = 50


def crawl_page(url):
    try:
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No title'
        links = [a['href'] for a in soup.find_all('a', href=True) if a['href'].startswith("http")]
        return {'url': url, 'title': title, 'links': links, 'error': None}
    except Exception as e:
        return {'url': url, 'title': None, 'links': [], 'error': str(e)}


def master_process(seed_urls):
    print(f"[Master] MPI Version: {MPI.Get_version()}")
    start_time = time.time()

    num_workers = size - 1
    pages_crawled = [0] * size
    visited = set()
    to_crawl = list(seed_urls)
    total_crawled = 0

    # Assign initial URLs to workers
    for i in range(1, min(num_workers + 1, len(to_crawl))):
        url = to_crawl.pop(0)
        visited.add(url)
        comm.send(url, dest=i, tag=11)

    active_workers = min(num_workers, len(seed_urls))

    while total_crawled < MAX_PAGES and active_workers > 0:
        data = comm.recv(source=MPI.ANY_SOURCE, tag=22)
        sender = data['worker']
        result = data['result']
        pages_crawled[sender] += 1
        total_crawled += 1

        if result['error']:
            print(f"Worker {sender} error: {result['error']}")
        else:
            safe_output = f"Worker {sender}:\n  URL: {result['url']}\n  Title: {result['title']}\n  Links found: {len(result['links'])}\n"
            sys.stdout.buffer.write(safe_output.encode('utf-8', errors='replace'))
            sys.stdout.flush()


        # Add new links to the queue (if not visited)
        for link in result['links']:
            if link not in visited and len(to_crawl) + total_crawled < MAX_PAGES:
                visited.add(link)
                to_crawl.append(link)

        # Assign new task or stop worker
        if to_crawl and total_crawled < MAX_PAGES:
            next_url = to_crawl.pop(0)
            visited.add(next_url)
            print(f"[Master] Sending URL to worker {sender}: {next_url}")
            comm.send(next_url, dest=sender, tag=11)
        else:
            comm.send(None, dest=sender, tag=0)
            active_workers -= 1

    total_time = time.time() - start_time
    print(f"Total crawl time: {total_time:.2f} seconds")
    print("Pages crawled by each worker:", pages_crawled[1:])
    print(f"Total pages crawled: {sum(pages_crawled)}")
    # writing stats to a file
    with open('crawl_results.txt', 'a') as f:
        f.write(f'Crawling results using MPI:\n')
        f.write(f'Number of workers: {num_workers}\n')
        f.write(f'Total time taken: {total_time:.2f} seconds\n')
        f.close()
    MPI.COMM_WORLD.Abort() # to end the MPI program


def worker_process():
    while True:
        status = MPI.Status()
        url = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        if status.Get_tag() == 0:
            break  # Exit signal
        result = crawl_page(url)
        comm.send({'worker': rank, 'result': result}, dest=0, tag=22)


if __name__ == "__main__":
    seed_urls = [
        "https://www.youtube.com",
        "https://www.coursera.org",
        "https://www.wikipedia.org",
        "https://www.stackoverflow.com",
        "https://www.python.org",
        "https://www.github.com",
    ]

    if rank == 0:
        master_process(seed_urls)
    else:
        worker_process()
