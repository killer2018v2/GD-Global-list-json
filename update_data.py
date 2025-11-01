# update_data.py
from scraper import DemonlistScraper

if __name__ == "__main__":
    print("🚀 Запускаю плановое обновление данных Demonlist...")
    scraper = DemonlistScraper()
    scraper.run()
    print("✅ Обновление успешно завершено!")