from flask import Flask, render_template
import m3u8
import requests
import logging
import json

app = Flask(__name__)

M3U8_URL = "https://vcnjltv.teleosmedia.com/vod/jltv/69e8c0bb-6a89-4f94-a6c1-f2d8cae05a47/playlist.m3u8"
AD_TAG_URL = "https://pubads.g.doubleclick.net/gampad/ads?iu=/21775744923/external/single_ad_samples&sz=640x480&cust_params=sample_ct%3Dlinear&ciu_szs=300x250%2C728x90&gdfp_req=1&output=vast&unviewed_position_start=1&env=vp&impl=s&correlator="

logging.basicConfig(level=logging.DEBUG)

def fetch_playlist(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

@app.route('/')
def index():
    logging.debug(f"Fetching master playlist from: {M3U8_URL}")
    master_content = fetch_playlist(M3U8_URL)
    master_playlist = m3u8.loads(master_content)

    first_playlist_uri = master_playlist.playlists[0].uri
    playlist_url = requests.compat.urljoin(M3U8_URL, first_playlist_uri)
    
    logging.debug(f"Fetching quality-specific playlist from: {playlist_url}")
    playlist_content = fetch_playlist(playlist_url)
    playlist = m3u8.loads(playlist_content)

    scte_markers = []
    total_duration = 0
    for i, segment in enumerate(playlist.segments):
        if segment.cue_out:
            scte_markers.append({
                'time': total_duration,
                'tag': f"#EXT-X-CUE-OUT:{segment.cue_out}"
            })
        if segment.cue_in:
            scte_markers.append({
                'time': total_duration,
                'tag': "#EXT-X-CUE-IN"
            })
        total_duration += segment.duration

    logging.info(f"Found {len(scte_markers)} SCTE markers")
    logging.debug(f"SCTE markers: {scte_markers}")

    return render_template('index.html', ad_tag_url=AD_TAG_URL, scte35_markers=json.dumps(scte_markers), m3u8_url=M3U8_URL)

if __name__ == '__main__':
    app.run(debug=True)
else:
    gunicorn_app = app
