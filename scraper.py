# scraper/scraper.py
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import json, re, time, os
from urllib.parse import urljoin
import settings

class DemonlistScraper:
    def __init__(self):
        self.data = []
        self.browser = None
        self.page = None

    def _safe_extract_name(self, text: str) -> str:
        text = text.strip()
        return text.split("-", 1)[1].strip() if "-" in text else text

    def _open_site(self, playwright):
        print("🌐 Открываю сайт Demonlist.org...")
        self.browser = playwright.chromium.launch(headless=settings.HEADLESS)
        self.page = self.browser.new_page()
        self.page.goto(settings.BASE_URL, wait_until="domcontentloaded", timeout=settings.PAGE_LOAD_TIMEOUT)
        self.page.wait_for_selector('div.w-\\[90\\%\\].mx-auto.grid.justify-items-center', timeout=settings.SELECTOR_TIMEOUT)
        time.sleep(2)

    def _reanimate_scroll(self):
        """'Раскачивает' страницу, если она перестала подгружать контент."""
        print("😴 Похоже, ленивая загрузка 'уснула'. Пробуем ее разбудить...")
        self.page.evaluate("window.scrollBy(0, -500);")
        time.sleep(0.5)
        self.page.evaluate("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(1)

    def _smart_scroll(self):
        """
        Умный скролл, который ждет подгрузки нового контента и борется с 'засыпанием' страницы.
        """
        print("📜 Начинаю умный скролл для загрузки всех уровней...")
        prev_count = self.page.evaluate("() => document.querySelectorAll('a[href^=\"/classic/\"]').length")
        no_new_attempts = 0

        while no_new_attempts < settings.MAX_NO_NEW_ATTEMPTS:
            # Делаем несколько быстрых скроллов
            for _ in range(settings.FAST_SCROLLS_PER_STEP):
                self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                time.sleep(0.3)

            # Терпеливо ждем появления нового контента
            start_time = time.time()
            found_new_in_cycle = False
            while time.time() - start_time < settings.MAX_WAIT_FOR_NEW:
                time.sleep(settings.SCROLL_PAUSE)
                new_count = self.page.evaluate("() => document.querySelectorAll('a[href^=\"/classic/\"]').length")
                if new_count > prev_count:
                    print(f"🔽 Найдено карточек: {new_count}")
                    prev_count = new_count
                    no_new_attempts = 0  # Сбрасываем счетчик неудач
                    found_new_in_cycle = True
                    break # Выходим из цикла ожидания

            # Если за все время ожидания ничего не появилось
            if not found_new_in_cycle:
                no_new_attempts += 1
                print(f"⏱ Нет новых карточек ({no_new_attempts}/{settings.MAX_NO_NEW_ATTEMPTS})")
                self._reanimate_scroll() # Пытаемся "разбудить" страницу
        
        print(f"✅ Скролл завершён. Всего найдено {prev_count} карточек.")


    def _extract_levels_list(self):
        html = self.page.content()
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select('a[href^="/classic/"]')
        pattern = re.compile(r"/classic/(\d+)")
        for card in cards:
            href = card.get("href", "")
            match = pattern.search(href)
            if not match: continue
            rank = int(match.group(1))
            name_tag = card.select_one("p.font-bold")
            name_raw = name_tag.get_text(strip=True) if name_tag else ""
            self.data.append({"rank": rank, "name": self._safe_extract_name(name_raw), "link": urljoin(settings.BASE_URL, href)})
        self.data.sort(key=lambda x: x["rank"])
        print(f"🧩 Извлечено {len(self.data)} уровней из основного списка.")

    def _parse_level_details(self, soup: BeautifulSoup) -> dict:
        details = {"length": None, "objects": None, "version": None}
        label_tags = soup.find_all("p", class_="font-bold")
        for tag in label_tags:
            label_text = tag.get_text(strip=True).lower()
            value_tag = tag.find_next_sibling("p")
            if value_tag:
                value_text = value_tag.get_text(strip=True)
                if "length" in label_text: details["length"] = value_text
                elif "objects" in label_text: details["objects"] = int(value_text.replace(",", ""))
                elif "version" in label_text: details["version"] = value_text
        return details

    def _scrape_all_details(self):
        print("\n🔎 Начинаю сбор детальной информации по каждому уровню (это займет время)...")
        for i, level in enumerate(self.data):
            link = level.get("link")
            print(f"[{i+1}/{len(self.data)}] Загружаю: #{level['rank']} {level['name']}")
            try:
                self.page.goto(link, wait_until="domcontentloaded", timeout=settings.PAGE_LOAD_TIMEOUT)
                # Увеличиваем таймаут ожидания селектора, чтобы дать странице больше времени
                self.page.wait_for_selector('p.font-bold', timeout=15000)
                # Даем еще полсекунды на всякий случай, если есть какие-то анимации
                time.sleep(0.5)
                details = self._parse_level_details(BeautifulSoup(self.page.content(), "html.parser"))
                level.update(details)
            except PlaywrightTimeoutError:
                print(f"❌ Тайм-аут при загрузке страницы для уровня #{level['rank']}. Пропускаю.")
            except Exception as e:
                print(f"❌ Ошибка при обработке уровня #{level['rank']}: {e}")

    def _save(self):
        os.makedirs(os.path.dirname(settings.OUTPUT_FILE), exist_ok=True)
        with open(settings.OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Данные сохранены в {settings.OUTPUT_FILE}")

    def run(self):
        with sync_playwright() as p:
            self._open_site(p)
            self._smart_scroll()
            self._extract_levels_list()
            self._scrape_all_details()
            self.browser.close()
        self._save()