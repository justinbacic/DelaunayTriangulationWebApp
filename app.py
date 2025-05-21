from flask import Flask, render_template, request, jsonify
import triangulation as tri

app = Flask(__name__)

# Store points in memory (in a real app, use a database)
points = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_point', methods=['POST'])
def save_point():
    data = request.get_json()
    x = round(data['x'],2)
    y = round(data['y'],2)
    points.append((x, y))
    return jsonify(success=True)

@app.route('/get_points', methods=['GET'])
def get_points():
    return jsonify(points=points)

@app.route('/clear_points', methods=['POST'])
def clear_points():
    global points
    points = []
    return jsonify(success=True)
@app.route('/get_drawing_sequence', methods=['GET'])
def get_drawing_sequence():
    triang = tri.Triangulation(points)
    records = triang.incremental_delaunay()
    drawing_sequence = []
    for i in records:
        print(i)
        drawing_sequence.append(triang.convert_record(i))
    return jsonify(drawing_sequence)
'''@app.route('/get_predefined_data', methods=['GET'])
def get_predefined_data():
    triang = tri.Triangulation(points)
    records = triang.incremental_delaunay()
    record = records[0]
    predefined_points = []
    for i in record["inserted"]:
        predefined_points.append(i)
    edges = []
    for i in record["edges"]:
        cur_edge = []
        for j in i:
            cur_edge.append(j)
        edges.append(cur_edge)
    return jsonify({
        'points': points,
        'edges': edges
    })'''

if __name__ == '__main__':
    app.run(debug=True)