"""One-time helper: generates placeholder colored-shape PNGs into layers/
so the generator can be run end-to-end before real artwork is added."""
import math
from pathlib import Path

from PIL import Image, ImageDraw

SIZE = (512, 512)
LAYERS_DIR = Path(__file__).resolve().parent.parent / "layers"


def solid_background(color):
    return Image.new("RGBA", SIZE, color)


def circle_layer(color):
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 100
    draw.ellipse([margin, margin, SIZE[0] - margin, SIZE[1] - margin], fill=color)
    return img


def ring_layer(color, width=20):
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = 60
    draw.ellipse(
        [margin, margin, SIZE[0] - margin, SIZE[1] - margin],
        outline=color, width=width,
    )
    return img


def star_layer(color):
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy, r = SIZE[0] // 2, 140, 60
    points = []
    for i in range(10):
        angle = math.pi / 2 + i * math.pi / 5
        radius = r if i % 2 == 0 else r / 2.5
        points.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    draw.polygon(points, fill=color)
    return img


def save(img, folder_name, filename):
    folder = LAYERS_DIR / folder_name
    folder.mkdir(parents=True, exist_ok=True)
    img.save(folder / filename)


def main():
    save(solid_background((80, 150, 255, 255)), "1_Background", "Blue#30.png")
    save(solid_background((255, 120, 80, 255)), "1_Background", "Orange#30.png")
    save(solid_background((60, 60, 60, 255)), "1_Background", "Dark#10.png")

    save(circle_layer((240, 220, 180, 255)), "2_Body", "Tan#40.png")
    save(circle_layer((180, 140, 100, 255)), "2_Body", "Brown#30.png")
    save(circle_layer((255, 215, 0, 255)), "2_Body", "Gold#2.png")

    save(ring_layer((30, 30, 30, 255)), "3_Eyes", "Black#40.png")
    save(ring_layer((0, 150, 0, 255)), "3_Eyes", "Green#20.png")

    save(Image.new("RGBA", SIZE, (0, 0, 0, 0)), "4_Accessories", "None#50.png")
    save(star_layer((255, 0, 0, 255)), "4_Accessories", "Red_Star#15.png")
    save(star_layer((255, 215, 0, 255)), "4_Accessories", "Gold_Star#1.png")

    print(f"Demo trait assets written to {LAYERS_DIR}")


if __name__ == "__main__":
    main()
