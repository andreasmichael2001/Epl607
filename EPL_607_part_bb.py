from PIL import Image

# Image dimensions
WIDTH, HEIGHT = 1024, 720
FOCAL_LENGTH = 500  # camera projection parameter

# Set pixel
def set_pixel(image, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        image.putpixel((x, y), color)

# Edge function
def edge_function(x0, y0, x1, y1, x, y):
    return (y0 - y1) * x + (x1 - x0) * y + (x0 * y1 - x1 * y0)

# Triangle rasterization
def draw_triangle(image, x0, y0, x1, y1, x2, y2, color):
    min_x = max(min(x0, x1, x2), 0)
    max_x = min(max(x0, x1, x2), WIDTH - 1)
    min_y = max(min(y0, y1, y2), 0)
    max_y = min(max(y0, y1, y2), HEIGHT - 1)

    E1 = lambda x, y: edge_function(x1, y1, x2, y2, x, y)
    E2 = lambda x, y: edge_function(x2, y2, x0, y0, x, y)
    E3 = lambda x, y: edge_function(x0, y0, x1, y1, x, y)

    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            if E1(x, y) >= 0 and E2(x, y) >= 0 and E3(x, y) >= 0:
                set_pixel(image, x, y, color)

# Perspective projection function
def project_point(x, y, z):
    px = int((x / z) * FOCAL_LENGTH + WIDTH / 2)
    py = int((y / z) * FOCAL_LENGTH + HEIGHT / 2)
    return px, py, 1 / z

# Create blank image
image = Image.new("RGB", (WIDTH, HEIGHT), "white")

# 3D triangles: (x0,y0,z0,x1,y1,z1,x2,y2,z2)
triangles_3d = [
    (-1, -1, 3,  1, -1, 3,  0, 1, 3),   # Near triangle
    (-1, -1, 6,  1, -1, 6,  0, 1, 6),   # Far triangle
    (-2, -1, 4,  0, -1, 4, -1, 1, 4),   # Middle triangle
]

# Color palette
colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]

# Project and collect triangles with avg 1/z for depth sorting
projected_triangles = []
for i, tri in enumerate(triangles_3d):
    x0, y0, z0, x1, y1, z1, x2, y2, z2 = tri
    sx0, sy0, iz0 = project_point(x0, y0, z0)
    sx1, sy1, iz1 = project_point(x1, y1, z1)
    sx2, sy2, iz2 = project_point(x2, y2, z2)
    avg_depth = (iz0 + iz1 + iz2) / 3
    projected_triangles.append((avg_depth, (sx0, sy0, sx1, sy1, sx2, sy2), colors[i % len(colors)]))

# Sort triangles by 1/z (depth): far to near
projected_triangles.sort(key=lambda t: -t[0])

# Draw in sorted order
for _, (sx0, sy0, sx1, sy1, sx2, sy2), color in projected_triangles:
    draw_triangle(image, sx0, sy0, sx1, sy1, sx2, sy2, color)

# Save and show result
image.save("project_p2.png")
image.show()
