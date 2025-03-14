import logging
import os
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime


class ProjectLogger:
    """
    Простий логер для проекту, який записує логи у файл.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        """Реалізація патерну Singleton для логера"""
        if cls._instance is None:
            cls._instance = super(ProjectLogger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, log_file_path=None, log_level=logging.INFO):
        """
        Ініціалізує логер

        :param log_file_path: Шлях до файлу логів. Якщо None, буде створений файл з датою в імені
        :param log_level: Рівень логування (за замовчуванням INFO)
        """
        if self._initialized:
            return

        # Встановлюємо шлях до файлу логів
        if log_file_path is None:
            logs_dir = "logs"
            # Створюємо директорію для логів, якщо вона не існує
            if not os.path.exists(logs_dir):
                os.makedirs(logs_dir)
            current_date = datetime.now().strftime("%Y-%m-%d")
            log_file_path = os.path.join(logs_dir, f"app_log_{current_date}.log")

        # Налаштовуємо основний логер
        self.logger = logging.getLogger("project_logger")
        self.logger.setLevel(log_level)

        # Налаштовуємо форматування логів
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s"
        )

        # Налаштовуємо виведення логів у файл з ротацією опівночі
        # interval=1 - ротація кожен день
        # when='midnight' - ротація опівночі
        # backupCount=7 - зберігаємо лише 7 останніх файлів
        file_handler = TimedRotatingFileHandler(
            log_file_path,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        file_handler.suffix = "%Y-%m-%d.log"  # формат суфіксу для архівних файлів
        self.logger.addHandler(file_handler)

        # Додатково налаштовуємо виведення логів у консоль
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        self._initialized = True

        self.logger.info(
            f"Логер ініціалізовано. Логи записуються у файл: {log_file_path} з ротацією опівночі та зберіганням 7 останніх файлів")

    def get_logger(self):
        """Повертає екземпляр логера"""
        return self.logger


# Функції-обгортки для спрощеного використання логера

def get_logger():
    """Повертає глобальний екземпляр логера"""
    return ProjectLogger().get_logger()


def debug(message):
    """Логування повідомлення з рівнем DEBUG"""
    get_logger().debug(message)


def info(message):
    """Логування повідомлення з рівнем INFO"""
    get_logger().info(message)


def warning(message):
    """Логування повідомлення з рівнем WARNING"""
    get_logger().warning(message)


def error(message):
    """Логування повідомлення з рівнем ERROR"""
    get_logger().error(message)


def critical(message):
    """Логування повідомлення з рівнем CRITICAL"""
    get_logger().critical(message)