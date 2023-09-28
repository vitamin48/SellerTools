from flask import Flask, render_template, request, redirect, url_for, send_file
import pandas as pd
import numpy as np
import io

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        if uploaded_file.filename != '':
            # Загрузка данных из загруженного файла Excel
            df = pd.read_excel(uploaded_file, sheet_name="Шаблон")

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

            rename_columns = {'Ширина упаковки, мм*': 'Ширина упаковки, cм',
                              'Высота упаковки, мм*': 'Высота упаковки, cм',
                              'Длина упаковки, мм*': 'Длина упаковки, cм'}

            mdf = mdf.rename(columns=rename_columns)

            mdf['Ссылки на фото'] = mdf.apply(lambda row: row['Ссылка на главное фото*']
            if pd.isna(row['Ссылки на дополнительные фото']) else row['Ссылка на главное фото*'] + ';' +
                                                                  row['Ссылки на дополнительные фото'], axis=1)

            mdf.drop(columns=['Ссылка на главное фото*', 'Ссылки на дополнительные фото'], inplace=True)

            mdf['Остатки'] = ''

            # Создание выходного файла Excel в буфере
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            mdf.to_excel(writer, index=False)
            writer.close()
            output.seek(0)

            return send_file(output, as_attachment=True, download_name='converted_data.xlsx')

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
