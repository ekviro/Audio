import os
import glob
from collections import defaultdict


def simple_merge():
    """Простая версия для быстрого использования"""

    # Укажите здесь путь к вашей папке
    folder_path = "."  # текущая папка

    total_counts = defaultdict(int)

    for file_path in glob.glob(os.path.join(folder_path, "*.txt")):
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if ':' in line:
                    word, count = line.strip().split(':', 1)
                    total_counts[word.strip()] += int(count.strip())

    # Сохраняем результат
    with open('rating.txt', 'w', encoding='utf-8-sig') as f:
        for word, count in sorted(total_counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"{word}: {count}\n")

    print("Готово! Результат в файле rating.txt")



if __name__ == "__main__":
    simple_merge()