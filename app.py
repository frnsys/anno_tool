import json
from flask import Flask, request, render_template, jsonify

app = Flask(__name__, template_folder='./')
annos = json.load(open('annos.json', 'r'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        data = request.get_json()
        notes = data['notes']
        with open('notes.md', 'w') as f:
            f.write(notes)
        return jsonify(success=True)
    else:
        notes = open('notes.md', 'r').read()
    return render_template('template.html', annos=annos, notes=notes)

app.run(debug=True)