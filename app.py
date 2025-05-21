from flask import Flask, render_template, request, jsonify
from triangulation import Triangulation  # Your existing class
import json
import time

app = Flask(__name__)

# Global variable to store triangulation state
current_triangulation = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/init_triangulation', methods=['POST'])
def init_triangulation():
    global current_triangulation
    points_temp = request.get_json().get('points', [])
    points = []
    for i in points_temp:
        points.append((i[0],i[1]))
    current_triangulation = Triangulation(points=points, speed=0)
    current_triangulation.incremental_delaunay(getPoints=False)
    return jsonify({'status': 'success'})

@app.route('/get_triangulation_state', methods=['GET'])
def get_triangulation_state():
    if not current_triangulation:
        return jsonify({'error': 'No triangulation initialized'})
    
    # Convert the triangulation state to JSON-serializable format
    state = {
        'vertices': [(v.x, v.y) for v in current_triangulation.vertices],
        'edges': [],
        'faces': []
    }
    
    # Add edges (avoid duplicates by checking IDs)
    edge_ids = set()
    for edge in current_triangulation.half_edges:
        if edge.id not in edge_ids:
            state['edges'].append({
                'id': edge.id,
                'x1': edge.origin.x,
                'y1': edge.origin.y,
                'x2': edge.next.origin.x,
                'y2': edge.next.origin.y
            })
            edge_ids.add(edge.id)
    
    return jsonify(state)

if __name__ == '__main__':
    app.run(debug=True)