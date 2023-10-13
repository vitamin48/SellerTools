"""
Сравнить 2 списка. Если артикул 1531125 находится в строке p-5930062-kist-dlya-makiyaja-recise-eye-liner
"""
import os

current_directory = os.path.dirname(os.path.abspath(__file__))

with open(f'{current_directory}\\articles.txt', 'r', encoding='utf-8') as file:
    articles = [f'{line}'.rstrip() for line in file]

with open(f'{current_directory}\\url.txt', 'r', encoding='utf-8') as file:
    url = [f'{line}'.rstrip() for line in file]

# for art in articles:
#     for u in url:
#         if art in u:
#             print(u)

set1 = set(articles)
set2 = set(url)
#
# intersection = set1.intersection(set2)
# print()

# Создайте список для хранения пересекающихся элементов
intersection = []

# Переберите элементы из set1
for number in set1:
    # Проверьте, содержится ли число в тексте из set2
    for text in set2:
        if str(number) in text:
            intersection.append(number)
            break  # Если число найдено в тексте, перейдите к следующему числу

print(intersection)