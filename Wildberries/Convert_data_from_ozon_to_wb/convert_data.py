import pandas as pd
import numpy as np

file_path = r"E:\distrib\fx\шаблон 240923\ВХОДНЫЕ ДАННЫЕ 2023-09-24 Картон.xlsx"

# Прочитать файл Excel в DataFrame
df = pd.read_excel(file_path, sheet_name="Шаблон")
df_x = pd.read_excel(r"E:\distrib\fx\шаблон 240923\FP_3000175_3010119.xlsx")

# Убрать первую строку
df.drop(1, inplace=True)

# Удаляем определенные столбцы
drop_columns = [5, 6, 7, 8, 15, 16, 19, 20, 21, 22, 23, 25, 27, 28, 29, 31, 33, 34, 35, 36, 37, 38, 39]
# mdf = df.drop(df.columns[drop_columns], axis=1)
mdf = df.copy()
# Переносим полностью первую строку в названия столбцов
mdf.columns = mdf.iloc[0]
# Убрать первую строку
mdf = mdf[1:]
# Сбросить индекс
mdf.reset_index(drop=True, inplace=True)

# Преобразования данных

mdf['Ширина упаковки, мм*'] = mdf['Ширина упаковки, мм*'].astype(float)
mdf['Ширина упаковки, мм*'] = np.ceil(mdf['Ширина упаковки, мм*'] / 10).astype(int)

mdf['Высота упаковки, мм*'] = mdf['Высота упаковки, мм*'].astype(float)
mdf['Высота упаковки, мм*'] = np.ceil(mdf['Высота упаковки, мм*'] / 10).astype(int)

mdf['Длина упаковки, мм*'] = mdf['Длина упаковки, мм*'].astype(float)
mdf['Длина упаковки, мм*'] = np.ceil(mdf['Длина упаковки, мм*'] / 10).astype(int)

mdf['Ссылки на дополнительные фото'] = mdf['Ссылки на дополнительные фото'].str.replace('\n', ';')

rename_columns = {'Ширина упаковки, мм*': 'Ширина упаковки, cм', 'Высота упаковки, мм*': 'Высота упаковки, cм',
                  'Длина упаковки, мм*': 'Длина упаковки, cм'}

mdf = mdf.rename(columns=rename_columns)

mdf['Ссылки на фото'] = mdf.apply(lambda row: row['Ссылка на главное фото*']
if pd.isna(row['Ссылки на дополнительные фото']) else row['Ссылка на главное фото*'] + ';' +
                                                      row['Ссылки на дополнительные фото'], axis=1)

mdf.drop(columns=['Ссылка на главное фото*', 'Ссылки на дополнительные фото'], inplace=True)

mdf['Остатки'] = ''

result_df = mdf.merge(df_x[['Артикул', 'Остаток на Бежицкой 1Б']], left_on='Артикул*', right_on='Артикул', how='left')


mdf.to_excel('converted_data.xlsx', index=False)
