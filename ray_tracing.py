import numpy as np
import yaml
from PIL import Image

# Carregar Configurações do Arquivo YAML
with open('params.yaml', 'r') as file:
    config = yaml.safe_load(file)

# Configurações da Imagem
IMAGE_WIDTH = config['image']['width']
IMAGE_HEIGHT = config['image']['height']

# Configurações Básicas da Câmera
ASPECT_RATIO = IMAGE_WIDTH / IMAGE_HEIGHT
VIEWPORT_HEIGHT = config['camera']['viewport_height']
VIEWPORT_WIDTH = ASPECT_RATIO * VIEWPORT_HEIGHT
FOCAL_LENGTH = config['camera']['focal_length']

# Posição e Orientação da Câmera
CAMERA_ORIGIN = np.array([0.0, 0.0, 0.0])
HORIZONTAL_VECTOR = np.array([VIEWPORT_WIDTH, 0.0, 0.0])
VERTICAL_VECTOR = np.array([0.0, VIEWPORT_HEIGHT, 0.0])
LOWER_LEFT_CORNER = CAMERA_ORIGIN - HORIZONTAL_VECTOR / 2 - VERTICAL_VECTOR / 2 - np.array([0.0, 0.0, FOCAL_LENGTH])

# Raio e Centro da Esfera
SPHERE_CENTER = np.array(config['sphere']['center'])
SPHERE_RADIUS = config['sphere']['radius']

# Configurações do Plano
PLANE_POINT = np.array(config['plane']['point'])
PLANE_NORMAL = np.array(config['plane']['normal'])

# Configurações de Iluminação
AMBIENT_COLOR = np.array(config['lighting']['ambient_color'])
OBJECT_COLOR = np.array(config['lighting']['object_color'])
SPECULAR_COLOR = np.array(config['lighting']['specular_color'])
LIGHT_POSITION = np.array(config['lighting']['light_position'])
LIGHT_COLOR = np.array(config['lighting']['light_color'])
SHADOW_INTENSITY = config['lighting']['shadow_intensity']

# Função de Normalização Vetorial
def normalize(vector):
    norm = np.linalg.norm(vector)
    return vector / norm if norm != 0 else vector

# Determina o ponto de intersecção (se existir) do Raio com a Esfera
def ray_sphere_intersection(sphere_center, sphere_radius, ray_origin, ray_direction):
    oc = ray_origin - sphere_center
    a = np.dot(ray_direction, ray_direction)
    b = 2.0 * np.dot(oc, ray_direction)
    c = np.dot(oc, oc) - sphere_radius * sphere_radius
    discriminant = b * b - 4 * a * c
    if discriminant < 0:
        return -1.0
    else:
        return (-b - np.sqrt(discriminant)) / (2.0 * a)

# Determina o ponto de intersecção (se existir) do Raio com o Plano
def ray_plane_intersection(plane_point, plane_normal, ray_origin, ray_direction):
    denom = np.dot(plane_normal, ray_direction)
    if np.abs(denom) > 1e-6:
        t = np.dot(plane_point - ray_origin, plane_normal) / denom
        if t >= 0:
            return t
    return -1.0

# Função que implementa o modelo de iluminação Phong
def phong_lighting(ray_origin, ray_direction, intersection_t, normal):
    # Componente Ambiente
    ambient = AMBIENT_COLOR * OBJECT_COLOR

    # Componente Difusa
    light_direction = normalize(LIGHT_POSITION - (ray_origin + intersection_t * ray_direction))
    diffuse_intensity = np.dot(normal, light_direction)
    diffuse = np.clip(diffuse_intensity, 0, 1) * OBJECT_COLOR * LIGHT_COLOR

    # Componente Especular
    view_direction = normalize(-ray_direction)
    reflection_direction = normalize(2 * np.dot(light_direction, normal) * normal - light_direction)
    specular_intensity = np.dot(view_direction, reflection_direction) ** 32
    specular = np.clip(specular_intensity, 0, 1) * SPECULAR_COLOR * LIGHT_COLOR

    # Somando todas as componentes
    return np.clip(ambient + diffuse + specular, 0, 1)

# Função que calcula a cor do raio
def calculate_ray_color(ray_origin, ray_direction):
    sphere_t = ray_sphere_intersection(SPHERE_CENTER, SPHERE_RADIUS, ray_origin, ray_direction)
    plane_t = ray_plane_intersection(PLANE_POINT, PLANE_NORMAL, ray_origin, ray_direction)

    if sphere_t > 0 and (plane_t < 0 or sphere_t < plane_t):
        hit_point = ray_origin + sphere_t * ray_direction
        normal = normalize(hit_point - SPHERE_CENTER)
        color = phong_lighting(ray_origin, ray_direction, sphere_t, normal)
        return (color * 255).astype(np.uint8)

    if plane_t > 0:
        shadow_ray_origin = ray_origin + plane_t * ray_direction
        shadow_ray_direction = normalize(LIGHT_POSITION - shadow_ray_origin)
        shadow_sphere_t = ray_sphere_intersection(SPHERE_CENTER, SPHERE_RADIUS, shadow_ray_origin, shadow_ray_direction)
        
        color = np.array([0.8, 0.8, 0.8])  # Cor do plano (chão)
        if shadow_sphere_t > 0:
            color *= SHADOW_INTENSITY  # Aplica a sombra
        return (color * 255).astype(np.uint8)

    unit_direction = normalize(ray_direction)
    t = 0.5 * (unit_direction[1] + 1.0)
    background_color = (1.0 - t) * np.array([0.2, 0.2, 0.3]) + t * np.array([0.8, 0.8, 1.0])
    return (background_color * 255).astype(np.uint8)

# Função que gera a imagem
def generate_image():
    image = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8)
    for j in range(IMAGE_HEIGHT):
        for i in range(IMAGE_WIDTH):
            u = i / (IMAGE_WIDTH - 1)
            v = (IMAGE_HEIGHT - j - 1) / (IMAGE_HEIGHT - 1)  # Corrigindo a inversão vertical
            ray_direction = LOWER_LEFT_CORNER + u * HORIZONTAL_VECTOR + v * VERTICAL_VECTOR - CAMERA_ORIGIN
            color = calculate_ray_color(CAMERA_ORIGIN, ray_direction)
            image[j, i] = color
    return image

# Função que salva a imagem
def save_image(image, filename):
    Image.fromarray(image).save(filename)

if __name__ == '__main__':
    image = generate_image()
    save_image(image, 'sphere.png')
