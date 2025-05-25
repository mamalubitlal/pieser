import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Text, Float, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
import threading
from queue import Queue
import concurrent.futures

load_dotenv()

# Создаем базу данных
Base = declarative_base()
engine = create_engine('sqlite:///search_engine.db')
Session = sessionmaker(bind=engine)

class WebPage(Base):
    __tablename__ = 'webpages'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True)
    title = Column(String(500))
    content = Column(Text)
    timestamp = Column(Float)

# Создаем таблицы
Base.metadata.create_all(engine)

class WebCrawler:
    def __init__(self, start_url, max_pages=None):
        self.start_url = start_url
        self.max_pages = max_pages
        self.visited_urls = set()
        self.session = Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.lock = threading.Lock()

    def is_valid_url(self, url):
        try:
            result = urlparse(url)
            return all([result.scheme in ['http', 'https'], result.netloc])
        except:
            return False

    def extract_text(self, soup):
        for script in soup(["script", "style"]):
            script.decompose()
        return soup.get_text(separator=' ', strip=True)

    def url_exists(self, url):
        with self.lock:
            return self.session.query(WebPage).filter_by(url=url).first() is not None

    def save_page(self, url, title, text):
        with self.lock:
            try:
                webpage = WebPage(
                    url=url,
                    title=title,
                    content=text,
                    timestamp=time.time()
                )
                self.session.add(webpage)
                self.session.commit()
                return True
            except IntegrityError:
                self.session.rollback()
                return False

    def crawl(self):
        queue = Queue()
        queue.put(self.start_url)
        pages_processed = 0
        
        while not queue.empty() and (self.max_pages is None or pages_processed < self.max_pages):
            url = queue.get()
            
            if url in self.visited_urls or self.url_exists(url):
                continue
                
            try:
                print(f"[{self.start_url}] Обработка: {url}")
                response = requests.get(url, headers=self.headers, timeout=10)
                print(f"[{self.start_url}] Статус код: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"[{self.start_url}] Пропуск {url}: статус код {response.status_code}")
                    continue
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                text = self.extract_text(soup)
                title = soup.title.string if soup.title else url
                
                if self.save_page(url, title, text):
                    self.visited_urls.add(url)
                    pages_processed += 1
                    print(f"[{self.start_url}] Сохранено: {url} (Всего: {pages_processed})")
                
                links_found = 0
                for link in soup.find_all('a', href=True):
                    new_url = urljoin(url, link['href'])
                    if self.is_valid_url(new_url) and new_url not in self.visited_urls and not self.url_exists(new_url):
                        queue.put(new_url)
                        links_found += 1
                
                print(f"[{self.start_url}] Найдено новых ссылок: {links_found}")
                print(f"[{self.start_url}] Размер очереди: {queue.qsize()}")
                
                time.sleep(1)
                
            except requests.exceptions.RequestException as e:
                print(f"[{self.start_url}] Ошибка сети при обработке {url}: {str(e)}")
                continue
            except Exception as e:
                print(f"[{self.start_url}] Неожиданная ошибка при обработке {url}: {str(e)}")
                continue

def run_crawler(url):
    crawler = WebCrawler(url, max_pages=None)
    try:
        crawler.crawl()
    except KeyboardInterrupt:
        print(f"\nКраулинг {url} остановлен пользователем")
    finally:
        print(f"Всего обработано страниц для {url}: {len(crawler.visited_urls)}")

if __name__ == "__main__":
    print("Введите URL через пробел (например: https://www.python.org https://www.github.com):")
    urls = input().strip().split()
    
    if not urls:
        print("Не указано ни одного URL")
        exit(1)
    
    print(f"Запуск краулеров для {len(urls)} URL...")
    
    # Создаем пул потоков
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(urls)) as executor:
        # Запускаем краулер для каждого URL
        futures = [executor.submit(run_crawler, url) for url in urls]
        
        try:
            # Ждем завершения всех краулеров
            concurrent.futures.wait(futures)
        except KeyboardInterrupt:
            print("\nОстановка всех краулеров...")
            for future in futures:
                future.cancel() 