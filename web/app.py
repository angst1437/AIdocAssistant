from flask import Flask, render_template, request, send_file
from docx import Document
from io import BytesIO
from logic import builder, partition, datatypes


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('form.html')


@app.route('/generate', methods=['POST'])
def generate_doc():
    title = datatypes.TitleData(
        university_info=list(filter(lambda elem: elem.strip() != "",request.form.get('university-info').split('\n'))),
        work_type=request.form.get('work-type'),
        subject=request.form.get('work-subject'),
        theme=request.form.get('work-theme'),
        author=request.form.get('fullname'),
        group=request.form.get('group'),
        educator=request.form.get('educator'),
        city=request.form.get('city'),
    )


    doc_builder = builder.DocBuilder()

    # Добавляем содержимое
    doc_builder.title_builder(title)
    doc = doc_builder.get_doc()

    # Сохраняем в байтовый поток
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)

    # Отправляем файл пользователю
    return send_file(
        file_stream,
        as_attachment=True,
        download_name='generated_document.docx',
        mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )


if __name__ == '__main__':
    app.run(debug=True)