"""
Скрипт сохраняет и открывает значение объекта в бинарный файл.
Здесь же для быстроты реализован экспорт в excel
"""
import pickle
import os
import pandas as pd

d_save = {'a': 1, 'b': 2, 'c': 3}

# pickle.dump(d_save, open('file.sav', 'wb'))
print(os.getcwd())
script_directory = os.path.dirname(os.path.abspath(__file__))

file1 = pickle.load(open(f'{script_directory}\\result_data_1.sav', 'rb'))
file2 = pickle.load(open(f'{script_directory}\\result_data_2.sav', 'rb'))
file3 = pickle.load(open(f'{script_directory}\\result_data_3.sav', 'rb'))

# Создаем новый пустой список для объединения
merged_list = []

# Добавляем элементы из list1
merged_list.extend(file1)

# Добавляем элементы из list2
merged_list.extend(file2)

# Добавляем элементы из list3
merged_list.extend(file3)

# Преобразовать список во множество (удалит дубликаты)
# unique_set = set(tuple(sorted(d.items())) for d in merged_list)
unique_set = set(tuple(d.items()) for d in merged_list)

# Преобразовать множество обратно в список
unique_list = [dict(item) for item in unique_set]

df = pd.DataFrame(unique_list)


def create_xls(df):
    """Создание файла excel из 1-го DataFrame"""
    file_name = f'{script_directory}\\OM_stocks.xlsx'
    writer = pd.ExcelWriter(file_name, engine_kwargs={'options': {'strings_to_urls': False}})
    df.to_excel(writer, sheet_name='Остатки Офисмаг', index=False, na_rep='NaN', engine='openpyxl')
    # Auto-adjust columns'
    for column in df:
        column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
        col_idx = df.columns.get_loc(column)
        writer.sheets[f'{"Остатки Офисмаг"}'].set_column(col_idx, col_idx, column_width)
    # writer.sheets["OZON"].set_column(1, 1, 30)
    writer.close()
    print(f'Успешно создан файл: {file_name}')


create_xls(df)

print()
