from flask import Flask, request, jsonify, render_template
from App import *

app = Flask(__name__)
prover_app = App()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/axioms', methods=['GET', 'POST'])
def axioms():
    if request.method == 'POST':
        expression_str = request.form['expression']
        parser = Parser(expression_str, prover_app.keywords)
        expression = parser.parse()
        prover_app.axioms.append(expression)
        return jsonify({'message': f'Axiom {expression} added successfully!'})
    return jsonify([str(axiom) for axiom in prover_app.axioms])

@app.route('/axioms/<int:index>', methods=['DELETE'])
def delete_axiom(index):
    try:
        axiom = prover_app.axioms.pop(index)
        return jsonify({'message': f'Axiom {axiom} deleted successfully!'})
    except IndexError:
        return jsonify({'message': 'Invalid index'}), 400

@app.route('/prove', methods=['POST'])
def prove():
    expression_str = request.form['expression']
    parser = Parser(expression_str, prover_app.keywords)
    expression = parser.parse()
    output = []

    def output_callback(message):
        output.append(message)

    prover = Prover(prover_app.axioms, expression, output_callback)
    result = prover.prove()
    return jsonify({'result': result, 'output': output})

if __name__ == "__main__":
    app.run(debug=True)

