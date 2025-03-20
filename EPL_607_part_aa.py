from PIL import Image

# Image dimensions
WIDTH, HEIGHT = 1024, 720

# Define a function to set a pixel in the image
def set_pixel(image, x, y, color):
    if 0 <= x < WIDTH and 0 <= y < HEIGHT:
        image.putpixel((x, y), color)

# Function to compute the edge function
def edge_function(x0, y0, x1, y1, x, y):
    return (y0 - y1) * x + (x1 - x0) * y + (x0 * y1 - x1 * y0)

# Function to draw a triangle using edge equations
def draw_triangle(image, x0, y0, x1, y1, x2, y2, color):
    
    min_x = max(min(x0, x1, x2), 0)
    max_x = min(max(x0, x1, x2), WIDTH - 1)
    min_y = max(min(y0, y1, y2), 0)
    max_y = min(max(y0, y1, y2), HEIGHT - 1)

    # Compute edge function coefficients
    E1 = lambda x, y: edge_function(x1, y1, x2, y2, x, y)  
    E2 = lambda x, y: edge_function(x2, y2, x0, y0, x, y)  
    E3 = lambda x, y: edge_function(x0, y0, x1, y1, x, y)  

    # Rasterize triangle by evaluating edge equations within bounding box
    for y in range(min_y, max_y + 1):
        for x in range(min_x, max_x + 1):
            e1 = E1(x, y)
            e2 = E2(x, y)
            e3 = E3(x, y)

            
            if e1 >= 0 and e2 >= 0 and e3 >= 0:
                set_pixel(image, x, y, color)

# Create a blank image
image = Image.new("RGB", (WIDTH, HEIGHT), "white")

# Define triangle vertices,colour and image shown
x0, y0 = 200, 500
x1, y1 = 500, 100
x2, y2 = 800, 500
triangle_color = (0, 0, 255)  
draw_triangle(image, x0, y0, x1, y1, x2, y2, triangle_color)
image.save("image.png")
image.show()
