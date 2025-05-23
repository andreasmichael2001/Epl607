from PIL import Image
import pywavefront
import numpy as np
import math

# Image and projection settings
WIDTH, HEIGHT = 1024, 720
FOCAL_LENGTH = 500

# --- Shading classes ---
class Material:
    def __init__(self, diffuse, specular, shininess, mode="both"):
        self.diffuse = np.array(diffuse, dtype=float)
        self.specular = np.array(specular, dtype=float)
        self.shininess = shininess
        self.mode = mode  # "diffuse", "specular", or "both"


class Light:
    def __init__(self, position, intensity):
        self.position = np.array(position, dtype=float)
        self.intensity = np.array(intensity, dtype=float)


# Set pixel safely
def set_pixel(image, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        image.putpixel((x, y), color)


# Edge function for triangle filling
def edge_function(x0, y0, x1, y1, x, y):
    return (y0 - y1) * x + (x1 - x0) * y + (x0 * y1 - x1 * y0)


# Triangle rasterization with Gouraud shading
def draw_triangle_gouraud(image, pts, cols):
    (x0, y0), (x1, y1), (x2, y2) = pts
    c0, c1, c2 = cols

    min_x = max(min(x0, x1, x2), 0)
    max_x = min(max(x0, x1, x2), WIDTH - 1)
    min_y = max(min(y0, y1, y2), 0)
    max_y = min(max(y0, y1, y2), HEIGHT - 1)

    area = edge_function(x0, y0, x1, y1, x2, y2)
    if area == 0:
        return

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            w0 = edge_function(x1, y1, x2, y2, x, y)
            w1 = edge_function(x2, y2, x0, y0, x, y)
            w2 = edge_function(x0, y0, x1, y1, x, y)
            if w0 >= 0 and w1 >= 0 and w2 >= 0:
                w0 /= area
                w1 /= area
                w2 /= area
                color = w0 * c0 + w1 * c1 + w2 * c2
                color = tuple(np.clip(color, 0, 255).astype(np.uint8))
                set_pixel(image, x, y, color)


# Perspective projection with z-check
def project_point(x, y, z):
    if z <= 0.001:
        return None
    px = int((x / z) * FOCAL_LENGTH + WIDTH / 2)
    py = int((y / z) * FOCAL_LENGTH + HEIGHT / 2)
    return px, py, 1 / z


# Rotate around axes
def rotate_y(v, angle_degrees):
    angle = math.radians(angle_degrees)
    x, y, z = v
    x_new = x * math.cos(angle) + z * math.sin(angle)
    z_new = -x * math.sin(angle) + z * math.cos(angle)
    return np.array([x_new, y, z_new])

def rotate_x(v, angle_degrees):
    angle = math.radians(angle_degrees)
    x, y, z = v
    y_new = y * math.cos(angle) - z * math.sin(angle)
    z_new = y * math.sin(angle) + z * math.cos(angle)
    return np.array([x, y_new, z_new])


# Load model and compute vertex normals
def load_obj_model(file_path):
    scene = pywavefront.Wavefront(file_path, collect_faces=True)
    vertices = []
    triangles = []
    normal_dict = {}

    for name, mesh in scene.meshes.items():
        for face in mesh.faces:
            if len(face) != 3:
                continue
            tri = [scene.vertices[i][:3] for i in face]
            triangles.append((face, np.array(tri)))
            for i in face:
                vertices.append(scene.vertices[i][:3])

            # Compute flat normal for triangle
            v0, v1, v2 = [np.array(scene.vertices[i][:3]) for i in face]
            normal = np.cross(v1 - v0, v2 - v0)
            normal = normal / np.linalg.norm(normal) if np.linalg.norm(normal) > 0 else normal
            for i in face:
                normal_dict.setdefault(i, []).append(normal)

    # Compute vertex normals
    vertex_normals = {}
    for idx, normals in normal_dict.items():
        avg_normal = np.mean(normals, axis=0)
        norm = np.linalg.norm(avg_normal)
        vertex_normals[idx] = avg_normal / norm if norm > 0 else avg_normal

    # Normalize and transform
    vertices = np.array(vertices)
    center = vertices.mean(axis=0)
    max_range = np.max(np.linalg.norm(vertices - center, axis=1))
    scale = 1.0 / max_range * 1.5

    transformed_data = []
    for face, tri in triangles:
        transformed_tri = []
        transformed_norms = []
        for i in face:
            v = np.array(scene.vertices[i][:3])
            n = vertex_normals[i]
            v_centered = (v - center) * scale
            v_rotated = rotate_y(v_centered, -130)
            v_rotated = rotate_x(v_rotated, 180)
            v_translated = v_rotated + np.array([0, -0.5, 5])
            transformed_tri.append(v_translated)
            transformed_norms.append(n)
        transformed_data.append((np.array(transformed_tri), np.array(transformed_norms)))

    return transformed_data


# Compute Phong lighting at a point
def phong_shading(pos, normal, material, light, view_pos):
    light_dir = light.position - pos
    light_dir = light_dir / np.linalg.norm(light_dir)
    view_dir = view_pos - pos
    view_dir = view_dir / np.linalg.norm(view_dir)
    reflect_dir = 2 * normal * np.dot(normal, light_dir) - light_dir
    reflect_dir = reflect_dir / np.linalg.norm(reflect_dir)

    ambient = 0.4 * material.diffuse
    diffuse = material.diffuse * max(np.dot(normal, light_dir), 0) if material.mode in ("diffuse", "both") else 0
    specular = material.specular * (max(np.dot(view_dir, reflect_dir), 0) ** material.shininess) if material.mode in ("specular", "both") else 0

    color = ambient + diffuse + specular
    return np.clip(color, 0, 255)


# Main rendering logic
if __name__ == "__main__":
    image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))  # light gray-blue background

    obj_file = "bunny.obj"
    model_data = load_obj_model(obj_file)

    material = Material(diffuse=[80, 130, 225], specular=[140, 140, 140], shininess=16, mode="both")
    light = Light(position=[0, 2, 5], intensity=np.array ([400, 400, 400]))
    light2 = Light(position=[0, -2, 5], intensity=np.array([200, 200, 200]))
    view_pos = np.array([0, 0, 0])

    projected_triangles = []
    for tri, norms in model_data:
        projected = [project_point(*v) for v in tri]
        if None in projected:
            continue

        screen_coords = [(p[0], p[1]) for p in projected]
        colors = [phong_shading(v, n, material, light, view_pos) for v, n in zip(tri, norms)]
        avg_depth = sum(p[2] for p in projected) / 3
        projected_triangles.append((avg_depth, screen_coords, colors))

    projected_triangles.sort(key=lambda t: -t[0])
    for _, coords, colors in projected_triangles:
        draw_triangle_gouraud(image, coords, colors)

    image.save("render_bunny_smooth.png")
    image.show()
