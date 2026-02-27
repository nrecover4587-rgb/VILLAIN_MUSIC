import os
import re
import aiofiles
import aiohttp
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont
from youtubesearchpython import VideosSearch


def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    newImage = image.resize((newWidth, newHeight))
    return newImage


async def get_thumb(videoid):
    try:
        if os.path.isfile(f"cache/{videoid}.png"):
            return f"cache/{videoid}.png"

        url = f"https://www.youtube.com/watch?v={videoid}"
        results = VideosSearch(url, limit=1)
        data = await results.next()

        if not data["result"]:
            return None

        result = data["result"][0]

        title = re.sub(r"\W+", " ", result.get("title", "Unsupported Title")).title()
        duration = result.get("duration", "Unknown")
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "Unknown Views")

        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status != 200:
                    return None
                content = await resp.read()

        os.makedirs("cache", exist_ok=True)

        async with aiofiles.open(f"cache/thumb{videoid}.png", mode="wb") as f:
            await f.write(content)

        youtube = Image.open(f"cache/thumb{videoid}.png")

        image1 = changeImageSize(1280, 720, youtube)
        image1 = image1.filter(ImageFilter.GaussianBlur(20))
        image1 = ImageEnhance.Brightness(image1).enhance(0.4)

        thumb_width = 840
        thumb_height = 460
        youtube_thumb = youtube.resize((thumb_width, thumb_height))

        mask = Image.new("L", (thumb_width, thumb_height), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle(
            [(0, 0), (thumb_width, thumb_height)], radius=20, fill=255
        )
        youtube_thumb.putalpha(mask)

        center_x = 640
        center_y_img = 300
        thumb_x = center_x - (thumb_width // 2)
        thumb_y = center_y_img - (thumb_height // 2)

        image1.paste(youtube_thumb, (thumb_x, thumb_y), youtube_thumb)

        draw = ImageDraw.Draw(image1)

        try:
            font_title = ImageFont.truetype("arial.ttf", 45)
            font_details = ImageFont.truetype("arial.ttf", 30)
        except:
            font_title = ImageFont.load_default()
            font_details = ImageFont.load_default()

        if len(title) > 45:
            title = title[:45] + "..."

        w_title = draw.textlength(title, font=font_title)
        draw.text(
            ((1280 - w_title) / 2, thumb_y + thumb_height + 40),
            title,
            fill="white",
            font=font_title,
        )

        stats_text = f"YouTube • {views} • {duration}"
        w_stats = draw.textlength(stats_text, font=font_details)
        draw.text(
            ((1280 - w_stats) / 2, thumb_y + thumb_height + 100),
            stats_text,
            fill="yellow",
            font=font_details,
        )

        try:
            os.remove(f"cache/thumb{videoid}.png")
        except:
            pass

        final_path = f"cache/{videoid}.png"
        image1.save(final_path)

        return final_path

    except Exception as e:
        print("Thumbnail Error:", e)
        return None


async def get_qthumb(vidid):
    try:
        url = f"https://www.youtube.com/watch?v={vidid}"
        results = VideosSearch(url, limit=1)
        data = await results.next()

        if not data["result"]:
            return None

        thumbnail = data["result"][0]["thumbnails"][0]["url"].split("?")[0]
        return thumbnail

    except Exception as e:
        print("Quick Thumb Error:", e)
        return None
