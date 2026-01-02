import json
import os
import datetime
import instaloader

# Configuration: Map Trail Name to Instagram Username
# NOTE: Using public web access or strict login is tricky. 
# For GitHub Actions, we might use a session file or just public access if possible (often blocked).
# Alternative: Use "rss.app" feeds if the user has them (some were in trails.dart), 
# or use a lighter scraping approach for just the latest caption.

# MAPPING extracted from trails.dart:
TRAIL_config = {
    "Traily Biely Kríž": "trailbielykriz", # guesswork, need to verify
    "Baťove traily": "batovetraily",
    "Bikepark Kálnica": "bikeparkkalnica",
    "Trail park Dolní Morava": "dolnimorava", # ?
    "Nitrails": "nitrails",
    "Bojnické traily": "hornonitrianske_stopy_bojnice", # check web
    "Bikepark Jasenská": "bikeparkjasenska",
    "Žilina Oko Trails": "okotrails",
    "Laskomerské singletraily": "laskomerske_singletraily", # check facebook/ig
    "Malinô Brdo Bikepark": "bikepark_malino_brdo", # check
    "Kubínska Hoľa Bikepark": "bikeparkkubinska",
    "Bachledka Bike Park": "bachledka_ski_sun",
    "Bikepark Mýto pod Ďumbierom": "kopeczabavy",
    "Bikepark Drozdovo": "skidrozdovo_bikepark",
    "Babské Traily": "babske_traily",
    "DIVO Traily": "divo_traily",
    "Bikepark Koliba": "bikeparkkoliba",
    "KeCy Košické Cyklotraily": "kecy_kosicke_cyklotraily",
}

# Placeholder for the actual scraping logic
# We will ideally use `instaloader` in the GitHub Action.

def mock_scrape():
    """
    Creates a dummy JSON structure for testing the UI.
    In the real GitHub Action, this will be replaced by actual scraping.
    """
    results = {}
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    display_names = {
        "Bikepark Kálnica": "bikeparkkalnica",
        "Traily Biely Kríž": "_trailbk",
        "Baťove traily": "batovetraily",
        "Bikepark Drozdovo": "bikeparkdrozdovo",
        "Bojnické traily": "hornonitrianskestopy",
        "DIVO Traily": "divotrailytrencin",
        "Bikepark Jasenská": "bikepark_jasenska",
        "Žilina Oko Trails": "zilina_okotrails",
        "Malinô Brdo Bikepark": "bikepark_malino_brdo",
        "Trail park Žehra": "trailparkzehra",
        "Babské Traily": "babske_traily",
        "KeCy Košické Cyklotraily": "kecy_kosicke_cyklotraily"
    }

    # Initialize Instaloader
    try:
        L = instaloader.Instaloader()
        
        # Load session from env var if available (GitHub Action)
        session_data = os.environ.get("IG_SESSION_DATA")
        session_user = os.environ.get("IG_SESSION_USER")
        
        if session_data and session_user:
            import base64
            # Decode session file content
            try:
                # We expect base64 encoded bytes of the session file
                session_bytes = base64.b64decode(session_data)
                
                # Instaloader expects a file named 'session-{username}'
                session_filename = f"session-{session_user}"
                with open(session_filename, "wb") as f:
                    f.write(session_bytes)
                
                print(f"Decoding session for {session_user}...")
                L.load_session_from_file(session_user, filename=session_filename)
                print("Session loaded successfully!")
            except Exception as e:
                print(f"Error loading session from env: {e}")
        
    except Exception as e:
        print(f"Instaloader error init: {e}")
        L = None

    for trail_name, handle in TRAIL_config.items():
        # Only scrape the ones we have specific handles for in display_names (active set)
        if trail_name in display_names and L:
            target_handle = display_names[trail_name]
            print(f"Scraping real data for {trail_name} (@{target_handle})...")
            try:
                profile = instaloader.Profile.from_username(L.context, target_handle)
                posts = profile.get_posts()
                
                # Fetch top 10 posts to have enough candidates after filtering pinned/old
                candidates = []
                count = 0
                for p in posts:
                    candidates.append(p)
                    count += 1
                    if count >= 10: break
                
                if not candidates:
                    raise Exception("No posts found")

                # Sort by date descending (newest first)
                candidates.sort(key=lambda x: x.date_local, reverse=True)
                
                # Take top 7
                final_posts = candidates[:7]

                posts_data = []
                # Ensure directory exists
                os.makedirs("assets/data/instagram", exist_ok=True)
                
                for post in final_posts:
                    # Download Image
                    img_url = post.url
                    local_filename = f"{post.shortcode}.jpg"
                    local_path = os.path.join("assets/data/instagram", local_filename)
                    
                    try:
                        # Use requests to download
                        import requests
                        response = requests.get(img_url, timeout=10)
                        if response.status_code == 200:
                            with open(local_path, "wb") as f:
                                f.write(response.content)
                            final_image_url = local_path
                        else:
                            print(f"    Failed to download image: {response.status_code}")
                            final_image_url = img_url # Fallback to remote if download fails
                    except Exception as e:
                        print(f"    Download error: {e}")
                        final_image_url = img_url

                    posts_data.append({
                        "caption": post.caption if post.caption else "Bez popisu",
                        "date": post.date_local.strftime("%Y-%m-%d %H:%M"),
                        "timestamp": int(post.date_local.timestamp()), 
                        "url": f"https://www.instagram.com/p/{post.shortcode}/",
                        "image_url": final_image_url 
                    })

                results[trail_name] = {
                    "username": target_handle,
                    "posts": posts_data
                }
                print(f"  -> Success! Found {len(posts_data)} posts for {trail_name}. Images downloaded.")
            except Exception as e:
                print(f"  -> Error scraping {target_handle}: {e}")
                results[trail_name] = {
                    "username": target_handle,
                    "posts": []
                }
        else:
            # Keep mock for others
             results[trail_name] = {
                "username": handle,
                "posts": [
                    {
                        "caption": f"Aktuálny stav pre {trail_name}: Dnes (sobota) otvorené! Traily sú suché... 🚵‍♂️☀️",
                        "date": timestamp,
                        "timestamp": int(datetime.datetime.now().timestamp()),
                        "url": f"https://instagram.com/{handle}",
                        "image_url": "PLACEHOLDER_FOR_UI_TEST" 
                    }
                ]
            }
    
    os.makedirs("assets/data", exist_ok=True)
    with open("assets/data/instagram_feed.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("MOCK Data generated in assets/data/instagram_feed.json")

if __name__ == "__main__":
    mock_scrape()
