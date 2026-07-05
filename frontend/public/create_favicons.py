from PIL import Image, ImageDraw
import os

# Define colors
THEME_BLUE = (0, 86, 210)  # #0056D2
WHITE = (255, 255, 255)

# Create 16x16 favicon
img_16 = Image.new('RGB', (16, 16), THEME_BLUE)
draw_16 = ImageDraw.Draw(img_16)
draw_16.text((2, 1), "M", fill=WHITE, font=None)
img_16.save('favicon-16x16.png')
print("✓ Created favicon-16x16.png")

# Create 32x32 favicon
img_32 = Image.new('RGB', (32, 32), THEME_BLUE)
draw_32 = ImageDraw.Draw(img_32)
draw_32.text((6, 4), "M", fill=WHITE, font=None)
img_32.save('favicon-32x32.png')
print("✓ Created favicon-32x32.png")

# Create 180x180 apple touch icon
img_apple = Image.new('RGB', (180, 180), THEME_BLUE)
draw_apple = ImageDraw.Draw(img_apple)
draw_apple.text((60, 60), "M", fill=WHITE, font=None)
img_apple.save('apple-touch-icon.png')
print("✓ Created apple-touch-icon.png")

# Create favicon.ico (using 32x32 as base)
img_32.save('favicon.ico')
print("✓ Created favicon.ico")

print("\n✅ All favicon files created successfully!")
