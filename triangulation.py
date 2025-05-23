import math
import time
import tkinter as tk
from tkinter import messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
from numpy import random
import numpy as np
'''This is a version of the Triangulation.py file that has been modified so that the triangulation class 
has a display attirbute which it can use to update the visualization of a triangulation.
For better comments on the Triangulation algorithm check the Triangulation.py file'''
class Vertex:
    """Represents a vertex in the DCEL."""
    def __init__(self, x, y):
        self.x = x  # Coordinates
        self.y = y
        self.incident_edge = None  # Pointer to an arbitrary outgoing half-edge
        self.incident_edges = set()
        self.visualization = False

    def __repr__(self):
        return f"({self.x}, {self.y})"


class HalfEdge:
    """Represents a half-edge in the DCEL."""
    def __init__(self,id=-1):
        self.origin = None       # Vertex where this half-edge starts
        self.twin = None         # Twin half-edge in the opposite direction
        self.next = None         # Next half-edge in the face
        self.prev = None         # Previous half-edge in the face
        self.face = None  # Face to the left of this half-edge
        self.id = id
    def toString(self):
        return f"!D: {self.id} {self.origin} -> {self.next.origin})"
    def __repr__(self):
        if self.twin is not None:
            return f"ID: {self.id} {self.origin} -> {self.next.origin}, Twin {self.twin.toString()}"
        return f"ID: {self.id} {self.origin} -> {self.next.origin}"


class Face:
    """Represents a face (triangular region) in the DCEL."""
    def __init__(self,id=-1):
        self.outer_component = None  # Pointer to a half-edge on the outer boundary
        self.inner_components = []   # List of half-edges for holes (empty for normal triangles)
        self.id = id
    def isEqual(self, other):
        return self.getPoints() == other.getPoints()
    def getPoints(self):
        points = []
        points.append(self.outer_component)
        points.append(self.outer_component.next)
        points.append(self.outer_component.prev)
        return points
    def __repr__(self):
        ret = "ID:"+str(self.id)+"\n"
        for i in self.getPoints():
            ret = ret + str(i) + "\n"
        ret = ret + str(self.outer_component) +"\n"
        return ret


class Triangulation:
    def __init__(self, points=None,speed = 1):
        self.vertices = []  # Stores Vertex objects
        self.half_edges = []  # Stores HalfEdge objects
        self.faces = []  # Stores Face objects
        if(points is not None):
            self.uninserted_points = list(points)  # Points not yet inserted
        else:
            self.uninserted_points = None
        self.point_triangle_map = {}  # Maps points to containing triangles
        self.triangle_point_map = {}  # Maps triangles to points inside
        self.curFaceID = 1
        self.curEdgeID = 1
        self.curVertexID = 1
        # Create a supertriangle to contain all points
        self.Tricount = 1
        self.Edgecount = 3
        self.root = tk.Tk()
        self.record = []
        self.updates = 0
        self.speed = speed
        self.supertriangle_edges = []

    def update_plot(self,circle = None,last=False):
        new_step = {}
        #new_step["step"] = self.updates
        self.updates = self.updates + 1
        inserted_points = []
        for i in self.vertices:
            inserted_points.append((i.x,i.y))
        new_step["inserted"] = inserted_points
        uninserted = []
        for i in self.uninserted_points:
            uninserted.append(i)
        new_step["uninserted"] = uninserted
        edges = []
        edges.extend(self.supertriangle_edges)
        for i in self.half_edges:
            if i.twin:
                cur_edge = set()
                cur_edge.add((i.origin.x,i.origin.y))
                cur_edge.add((i.twin.origin.x,i.twin.origin.y))
                if cur_edge not in edges:
                    edges.append(cur_edge)
        new_step["edges"] = edges
        if circle is not None:
            new_step["circle"] = [circle]
        else:
            new_step["circle"] = []
        if new_step not in self.record or last:
            self.record.append(new_step)
        

    def create_supertriangle(self):
        """Creates a supertriangle large enough to contain all points."""
        min_x = min(p[0] for p in self.uninserted_points)
        max_x = max(p[0] for p in self.uninserted_points)
        min_y = min(p[1] for p in self.uninserted_points)
        max_y = max(p[1] for p in self.uninserted_points)

        dx, dy = max_x - min_x, max_y - min_y
        delta_max = max(dx, dy) *1.1

        v2 = self.insert_point(round(min_x - delta_max,2), round(max_y + delta_max/2,2))
        v1 = self.insert_point(round(max_x + delta_max,2), round(max_y + delta_max/2,2))
        v3 = self.insert_point(round((min_x + max_x) / 2,2), round(min_y - delta_max,2))

        self.insert_triangle(v1, v2, v3)
        edge1 = set([(v1.x,v1.y),(v2.x,v2.y)])
        edge2 = set([(v1.x,v1.y),(v3.x,v3.y)])
        edge3 = set([(v2.x,v2.y),(v3.x,v3.y)])
        self.supertriangle_edges.extend([edge1,edge2,edge3])
        # Assign all uninserted points to this supertriangle
        supertriangle = self.faces[0]
        pointsInTriangle = set()
        for point in self.uninserted_points:
            self.point_triangle_map[point] = supertriangle
            pointsInTriangle.add(point)
        #Map triangle to all points
        self.triangle_point_map[supertriangle] = pointsInTriangle
        self.update_plot()


    def insert_point(self, x, y):
        """Inserts a new vertex into the triangulation."""
        vertex = Vertex(x, y)
        self.vertices.append(vertex)
        return vertex


    def insert_triangle(self, v1, v2, v3):
        """Inserts a new triangle into the DCEL."""
        e1 = HalfEdge(self.curEdgeID)
        self.curEdgeID += 1
        e2 = HalfEdge(self.curEdgeID)
        self.curEdgeID += 1
        e3 = HalfEdge(self.curEdgeID)
        self.curEdgeID += 1
        e1.origin, e2.origin, e3.origin = v1, v2, v3
        e1.next, e2.next, e3.next = e2, e3, e1
        e1.prev, e2.prev, e3.prev = e3, e1, e2
        #print("For vertices",v1, v2, v3,"\nEdge 1: ",e1,"\nEdge 2: ",e2,"\nEdge 3: ",e3,"\n")
        # Add the new edges to the incident_edges set of the vertices
        v1.incident_edges.add(e1)
        v2.incident_edges.add(e2)
        v3.incident_edges.add(e3)

        face = Face(self.curFaceID)
        self.curFaceID += 1
        face.outer_component = e1
        e1.face = e2.face = e3.face = face
        self.half_edges.extend([e1, e2, e3])
        #print("Adding edges in insert_triangulation: ", e1, e2, e3)
        self.faces.append(face)
        

        return face
    def insert_new_triangle(self, v1, v2, v3):
        """Inserts a new triangle into the DCEL."""
        e1Existed = False
        e1 = None
        for i in v1.incident_edges:
            if i.next.origin == v2:
                e1 = i
                e1Existed = True
        if e1 is None:
            e1 = HalfEdge(self.curEdgeID)
            self.curEdgeID += 1
        e2 = HalfEdge(self.curEdgeID)
        self.curEdgeID += 1
        e3 = HalfEdge(self.curEdgeID)
        self.curEdgeID += 1
        e1.origin, e2.origin, e3.origin = v1, v2, v3
        e1.next, e2.next, e3.next = e2, e3, e1
        e1.prev, e2.prev, e3.prev = e3, e1, e2

        # Add the new edges to the incident_edges set of the vertices
        v1.incident_edges.add(e1)
        v2.incident_edges.add(e2)
        v3.incident_edges.add(e3)

        face = Face(self.curFaceID)
        self.curFaceID += 1
        face.outer_component = e1
        e1.face = e2.face = e3.face = face
        if e1Existed:
            self.half_edges.extend([e2, e3])
            #print("Inserting edges in insert new triangulation: ", e1, e2, e3)
            self.Edgecount += 2
        else:
            self.half_edges.extend([e1, e2, e3])
            #print("Inserting edges in insert new triangulation else: ", e1, e2, e3)
            self.Edgecount += 3
        self.faces.append(face)
        self.Tricount += 1
        #print("Adding triangle",face,"\n")
        return face
    def linkTriangles(self, t1, t2, t3):
        e11 = t1.outer_component
        e21 = e11.next
        e31 = e11.prev
        e12 = t2.outer_component
        e22 = e12.next
        e32 = e12.prev
        e13 = t3.outer_component
        e23 = e13.next
        e33 = e13.prev
        e21.twin = e32
        e32.twin = e21
        e31.twin = e23
        e23.twin = e31
        e22.twin = e33
        e33.twin = e22
    def find_containing_triangle(self, point):
        return self.point_triangle_map[point]
    
    def updateBuckets(self, face, point, t1, t2, t3):
        pointsOfInterest = self.triangle_point_map.get(face)
        pointsOfInterest.remove(point)
        if(t1 not in self.triangle_point_map):
            pointSet = set()      
            self.triangle_point_map[t1] = pointSet
        if(t2 not in self.triangle_point_map):
            pointSet = set()      
            self.triangle_point_map[t2] = pointSet
        if(t3 not in self.triangle_point_map):
            pointSet = set()      
            self.triangle_point_map[t3] = pointSet
        for i in pointsOfInterest:
            if self.point_triangle_map[i] in self.faces:
                continue
            if(self.is_point_in_triangle(i,t1)):
                self.point_triangle_map[i] = t1
                pointSet = self.triangle_point_map[t1]
                pointSet.add(i)
                self.triangle_point_map[t1] = pointSet
            elif(self.is_point_in_triangle(i,t2)):
                self.point_triangle_map[i] = t2
                pointSet = self.triangle_point_map[t2]
                pointSet.add(i)
                self.triangle_point_map[t2] = pointSet
            elif(self.is_point_in_triangle(i,t3)):
                self.point_triangle_map[i] = t3
                pointSet = self.triangle_point_map[t3]
                pointSet.add(i)
                self.triangle_point_map[t3] = pointSet

    def updateBucketsForFlip(self, face1, face2, t1, t2):
        if(t1 not in self.triangle_point_map):
            pointSet = set()      
            self.triangle_point_map[t1] = pointSet
        if(t2 not in self.triangle_point_map):
            pointSet = set()      
            self.triangle_point_map[t2] = pointSet
        pointsOfInterest = self.triangle_point_map.get(face1)
        for i in pointsOfInterest:
            if self.point_triangle_map[i] in self.faces:
                continue
            if(self.is_point_in_triangle(i,t1)):
                self.point_triangle_map[i] = t1
                pointSet = self.triangle_point_map[t1]
                pointSet.add(i)
                self.triangle_point_map[t1] = pointSet
            elif(self.is_point_in_triangle(i,t2)):
                self.point_triangle_map[i] = t2
                pointSet = self.triangle_point_map[t2]
                pointSet.add(i)
                self.triangle_point_map[t2] = pointSet
        pointsOfInterest = self.triangle_point_map.get(face2)
        for i in pointsOfInterest:
            if self.point_triangle_map[i] in self.faces:
                continue
            if(self.is_point_in_triangle(i,t1)):
                self.point_triangle_map[i] = t1
                pointSet = self.triangle_point_map[t1]
                pointSet.add(i)
                self.triangle_point_map[t1] = pointSet
            elif(self.is_point_in_triangle(i,t2)):
                self.point_triangle_map[i] = t2
                pointSet = self.triangle_point_map[t2]
                pointSet.add(i)
                self.triangle_point_map[t2] = pointSet
    def is_point_in_triangle(self, point, face):
        """Check if a point is inside a given triangle."""
        v1 = face.outer_component.origin
        v2 = face.outer_component.next.origin
        v3 = face.outer_component.next.next.origin
        return self.is_inside_triangle(point, v1, v2, v3)
    def flip_edge(self, edge):
        """Flips an edge if it violates the Delaunay condition and removes old edges."""
        twin = edge.twin
        if twin is None or twin.face is None:
            return  # True boundary edge (can't flip)

        # Get the four vertices involved in the flip
        a = edge.origin
        b = edge.next.origin
        c = edge.prev.origin
        d = twin.prev.origin

        # Check the in-circle condition before flipping
        if not self.in_circle(a, b, c, d):
            return  # No flip needed
        #self.update_plot()
        #plot_triangulation(self)
        face1 = edge.face
        face2 = twin.face
        
        # Perform the flip: swap the edge's origin with the twin's origin
        edge.origin = c
        twin.origin = d
        bc = edge.next
        ca = edge.prev
        ad = twin.next
        db = twin.prev
        a.incident_edges.remove(edge)
        b.incident_edges.remove(twin)
        # Reconnect the new edges to each other
        #correct edge db
        twin.prev.prev = edge
        twin.prev.next = bc
        #correct edge bc
        edge.next.prev = db
        edge.next.next = edge
        #correct edge ad
        twin.next.prev = ca
        twin.next.next = twin
        #correct edge ca
        edge.prev.prev = twin
        edge.prev.next = ad
        #correct twin
        twin.prev = ad
        twin.next = ca
        #correct edge
        edge.next = db
        edge.prev = bc
        
        #Add incident edges
        c.incident_edges.add(edge)
        d.incident_edges.add(twin)
        
        # Create new faces after the flip
        new_face1 = Face(self.curFaceID)
        self.curFaceID += 1
        new_face2 = Face(self.curFaceID)
        self.curFaceID += 1
        new_face1.outer_component = edge
        new_face2.outer_component = twin
        # Assign new faces to the edges
        edge.face, edge.next.face,edge.prev.face = new_face1, new_face1, new_face1
        twin.face, twin.next.face, twin.prev.face = new_face2, new_face2, new_face2
        # Remove the old faces from the list (only after they are fully disconnected)
        # This avoids issues where faces are removed multiple times or incorrectly.
        self.faces.remove(face1)
        self.faces.remove(face2)
        self.updateBucketsForFlip(face1,face2,new_face1,new_face2)
        # Add the new faces to the structure
        self.faces.append(new_face1)
        self.faces.append(new_face2)
        self.update_plot()
        # Recurse on the neighboring edges
        self.flip_edge(edge.next)
        self.flip_edge(edge.prev)
        self.flip_edge(twin.next)
        self.flip_edge(twin.prev)
        #print("\nFlipped an EDGE!!!!\n")
    def circumcenter(self,ax,ay,bx,by,cx,cy):
        d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
        ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
        uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
        return (round(ux,2), round(uy,2))
    def in_circle(self, a, b, c, d):
        """Returns True if point d is inside the circumcircle of triangle (a, b, c)."""
        ax, ay = a.x, a.y
        bx, by = b.x, b.y
        cx, cy = c.x, c.y
        dx, dy = d.x, d.y
        center_x, center_y = self.circumcenter(ax,ay,bx,by,cx,cy)
        self.update_plot((center_x,center_y,round(math.dist((a.x,a.y),(center_x,center_y)),0)))
        # Determinant method
        matrix = [
            [ax - dx, ay - dy, (ax - dx) ** 2 + (ay - dy) ** 2],
            [bx - dx, by - dy, (bx - dx) ** 2 + (by - dy) ** 2],
            [cx - dx, cy - dy, (cx - dx) ** 2 + (cy - dy) ** 2],
        ]

        det = (matrix[0][0] * (matrix[1][1] * matrix[2][2] - matrix[2][1] * matrix[1][2])
            - matrix[0][1] * (matrix[1][0] * matrix[2][2] - matrix[2][0] * matrix[1][2])
            + matrix[0][2] * (matrix[1][0] * matrix[2][1] - matrix[2][0] * matrix[1][1]))

        return det > 0  # If determinant > 0, d is inside the circumcircle

    def is_inside_triangle(self, p, a, b, c):
        """Barycentric method to check if a point is inside a triangle."""
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])

        d1 = sign(p, (a.x, a.y), (b.x, b.y))
        d2 = sign(p, (b.x, b.y), (c.x, c.y))
        d3 = sign(p, (c.x, c.y), (a.x, a.y))

        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)

        return not (has_neg and has_pos)

    def retriangulate(self, point):
        
        #print(self.point_triangle_map)
        """Performs local retriangulation after inserting a point."""
        triangle = self.find_containing_triangle(point)
        if not triangle:
            print(f"Error: No containing triangle found for {point}")
            return
        
        # Remove the old triangle and insert 3 new ones
        self.faces.remove(triangle)
        self.Tricount -= 1

        #Remove point from point map since it's not uninserted
        self.point_triangle_map.pop(point)
        
        v1 = triangle.outer_component.origin
        v2 = triangle.outer_component.next.origin
        v3 = triangle.outer_component.prev.origin
        p_vertex = self.insert_point(point[0], point[1])
        

        t1 = self.insert_new_triangle(v1, v2, p_vertex)
        t2 = self.insert_new_triangle(v2, v3, p_vertex)
        t3 = self.insert_new_triangle(v3, v1, p_vertex)
        self.linkTriangles(t1,t2,t3)
        self.updateBuckets(triangle, point, t1, t2, t3)
        self.triangle_point_map.pop(triangle)
        self.update_plot()
        # Flip edges if necessary
        for tri in [t1, t2, t3]:
            for edge in [tri.outer_component, tri.outer_component.next, tri.outer_component.prev]:
                self.flip_edge(edge)


    def incremental_delaunay(self,getPoints = True):
        self.create_supertriangle()
        """Performs incremental Delaunay triangulation."""
        while self.uninserted_points:
            point = self.uninserted_points.pop(0)
            self.retriangulate(point)
        self.update_plot(last=True)
        return self.record
    def print_edges(self):
        """Prints unique edges in the triangulation."""
        printed_edges = set()

        print("\nEdges:")
        for edge in self.half_edges:
            print("\n",edge)

    def print(self):
        """Prints the current DCEL structure."""
        print(self.faces)
    def checkValidity(self):
        if len(self.faces) != self.Tricount:
            print(f"Error {len(self.faces)} triangles, expected {self.Tricount}\n")
        else:
            print("Yessir\n")
        if len(self.half_edges) != self.Edgecount:
            print(f"Error {len(self.half_edges)} edges, expected {self.Edgecount}\n")
        else:
            print("Yessir\n")
    def convert_record(self, record):
        new_record = {}
        points = []
        for i in record["inserted"]:
            points.append(i)
        uninserted_points = []
        for i in record["uninserted"]:
            uninserted_points.append(i)
        edges = []
        for i in record["edges"]:
            cur_edge = []
            for j in i:
                cur_edge.append(j)
            edges.append(cur_edge)
        new_record["points"] = points
        new_record["edges"] = edges
        new_record["uninserted_points"] = uninserted_points
        new_record["circles"] = record["circle"]
        return new_record