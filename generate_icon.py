from PIL import Image, ImageDraw, ImageFont

def create_icon():
    size = (512, 512)
    img = Image.new('RGB', size, color='#1E1E24')
    draw = ImageDraw.Draw(img)
    try:
        # Windows uses arialbd.ttf
        font = ImageFont.truetype("arialbd.ttf", 120)
    except IOError:
        font = ImageFont.load_default()
        
    draw.rectangle([10, 10, 501, 501], outline="#8B5CF6", width=8)
    text = "MMSWC"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size[0] - text_width) / 2
    y = (size[1] - text_height) / 2
    draw.text((x, y), text, font=font, fill="#F8F8F2")
    
    img.save("mmswc_icon.png")
    img.save("mmswc_icon.ico", format="ICO")
    print("Icons created successfully!")

if __name__ == "__main__":
    create_icon()
