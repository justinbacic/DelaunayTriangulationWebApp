from flask import Flask, render_template, request, jsonify
import triangulation as tri

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_drawing_sequence', methods=['POST'])
def get_drawing_sequence():
    data = request.get_json()  # Get JSON data from request
    points = data['points']
    formatted_points = []
    for i in points:
        formatted_points.append((i["x"],i["y"]))
    triang = tri.Triangulation(formatted_points)
    records = triang.incremental_delaunay()
    drawing_sequence = []
    for i in records:
        drawing_sequence.append(triang.convert_record(i))
    return jsonify(drawing_sequence)

if __name__ == '__main__':
    app.run(debug=True)