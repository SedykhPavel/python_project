from bs4 import BeautifulSoup
import requests
import os
import shutil
import threading
import tkinter as tk
from tkinter import messagebox

class BaseImagenerate:
    def __init__(self, base_url, directory='Pictures'):
        self.base_url = base_url
        self.directory = directory
        self._prepare_directory() # Для подготовки файла загруженных картинок
        self.lock = threading.Lock()
        self.running = True  # Переменная для отслеживания состояния загрузки

    def _prepare_directory(self):
        if os.path.exists(self.directory):
            shutil.rmtree(self.directory)
        os.makedirs(self.directory)

    def load_images(self, pages=1):
        raise NotImplementedError()

class Imagenerator(BaseImagenerate):
    def load_images(self, pages=1): # 
        threads = []
        for page in range(1, pages + 1):
            if not self.running:
                break
            url = f'{self.base_url}?page={page}'
            thread = threading.Thread(target=self._load_img, args=(url,))
            threads.append(thread)
            thread.start()
        if len(threads) >= 3:
            for thread in threads:
                thread.join()
            threads = []

    def _load_img(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        threads = []
        for link in soup.find_all('a', "avatars__link"):
            if not self.running:
                break
            img_url = link.get('href')
            print(f'Идет загрузка изображения: {img_url}')
            thread = threading.Thread(target=self._download_image, args=(img_url,))
            threads.append(thread)
            thread.start()
        if len(threads) >= 3:
            for thread in threads:
                thread.join()
            threads = []

    def _download_image(self, img_url):
        img_response = requests.get(img_url, stream=True)
        name = img_url.split('/')[-1]
        file_path = os.path.join(self.directory, name)

        with self.lock:
            with open(file_path, 'bw') as file:
                for chunk in img_response.iter_content(4096):
                    file.write(chunk)
        print(f'Скачан файл: {file_path}')

    def stop_loading(self):
        self.running = False  # Остановка загрузки

class App:
    def __init__(self, window):
        self.window = window
        self.window.title("Imagenerator")
        self.window.geometry("500x300")
        self.window.configure(bg="#f0f0f0")

        self.label = tk.Label(window, text="Нажмите 'Начать' для загрузки изображений", bg="#f0f0f0", font=("Arial", 12))
        self.label.pack(pady=10)

        self.start_button = tk.Button(window, text="Начать", command=self.start_loading, bg="#4CAF50", fg="white")
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(window, text="Завершить", command=self.stop_loading, bg="#f44336", fg="white")
        self.stop_button.pack(pady=10)
        self.stop_button.config(state=tk.DISABLED) 

    def start_loading(self):
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)  
        messagebox.showinfo("Скачивание", "Начинается загрузка изображений...")

        self.loader = Imagenerator('https://cspromogame.ru/avatars')
        threading.Thread(target=self.run_loader).start()

    def run_loader(self):
        self.loader.load_images(pages=200)
        messagebox.showinfo("Завершено", "Загрузка изображений завершена!")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)  

    def stop_loading(self):
        self.loader.stop_loading()  # Остановка загрузки
        messagebox.showinfo("Завершение", "Загрузка изображений остановлена.")
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)  

if __name__ == "__main__":
    window = tk.Tk()
    app = App(window)
    window.mainloop()
