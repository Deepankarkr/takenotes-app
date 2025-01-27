from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import make_response
import markdown
import bleach


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



# Model for storing content
class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    markdown_text = db.Column(db.Text, nullable=False)
    html_text = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/')
def index():
    return redirect(url_for('input_content'))

@app.route('/input', methods=['GET', 'POST'])
def input_content():
    if request.method == 'POST':
        markdown_text = request.form['content']
        # Configure Markdown parser to handle newlines

        html_text = bleach.clean(
            markdown.markdown(markdown_text, extensions=['nl2br', 'extra']),
            tags=['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre'],
            strip=True
        )

        new_content = Content(markdown_text=markdown_text, html_text=html_text)
        db.session.add(new_content)
        db.session.commit()
        return redirect(url_for('display_content'))
    return render_template('input.html')

@app.route('/display', methods=['GET', 'POST'])
def display_content():
    contents = Content.query.order_by(Content.timestamp.desc()).all()
    return render_template('display.html', contents=contents)

@app.route('/delete/<int:id>')
def delete_content(id):
    content = Content.query.get_or_404(id)
    db.session.delete(content)
    db.session.commit()
    return redirect(url_for('display_content'))


@app.route('/export')
def export_content():
    contents = Content.query.order_by(Content.timestamp.desc()).all()
    markdown_text = ""

    for content in contents:
        markdown_text += f"{content.markdown_text}\n"
        markdown_text += "--- \n\n"

    response = make_response(markdown_text)
    response.headers["Content-Disposition"] = "attachment; filename=all_content.md"
    response.headers["Content-Type"] = "text/markdown"
    return response


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database and tables before starting the server
    app.run(debug=True)
