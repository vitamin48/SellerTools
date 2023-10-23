"""
Скрипт сохраняет значение объекта в бинарный файл
"""
import pickle

d_save = {'a': 1, 'b': 2, 'c': 3}

# pickle.dump(d_save, open('file.sav', 'wb'))

file = pickle.load(open('result_data.sav', 'rb'))
print()

