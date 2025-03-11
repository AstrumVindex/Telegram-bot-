from instaloader import Instaloader, Post

L = Instaloader()

async def download_media(url: str):
    shortcode = url.split("/")[-2]
    post = Post.from_shortcode(L.context, shortcode)
    L.download_post(post, target="downloads")
    return f"downloads/{post.shortcode}.mp4"  # Example return path
