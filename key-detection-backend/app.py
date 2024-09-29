import os
import librosa
import soundfile as sf
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from flask import Flask, request, jsonify
from tempfile import NamedTemporaryFile
import traceback
import numpy as np
import re
from flask_cors import CORS, cross_origin
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.url_map.strict_slashes = False

# Enable CORS for all routes and all domains, explicitly allowing necessary headers and methods
CORS(app)

# Spotify credentials (ensure these are in your .env file)
SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')

# Debugging print to verify credentials
print(f"Client ID: {SPOTIPY_CLIENT_ID}, Client Secret: {SPOTIPY_CLIENT_SECRET}")

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET
))

# Function to get Spotify key from the official API
def get_spotify_official_key(spotify_url: str):
    """Fetch the official key from Spotify's API."""
    try:
        # Extract track ID from Spotify URL
        track_id = spotify_url.split("/")[-1].split("?")[0]
        print(f"Track ID: {track_id}")  # Debugging print

        # Fetch the audio features for the track
        features = sp.audio_features(track_id)
        print(f"Spotify API Response: {features}")  # Debugging print

        if features and features[0]:  # Ensure the features are not None or empty
            key = features[0]['key']  # Key as an integer
            mode = features[0]['mode']  # 1 = major, 0 = minor

            # Key mapping to musical notation
            key_mapping = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F',
                           'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']
            musical_key = key_mapping[key]
            scale = 'major' if mode == 1 else 'minor'

            return f"{musical_key} {scale}"
        else:
            print("No features found.")  # Debugging print
            return None
    except Exception as e:
        print(f"Error fetching key from Spotify: {e}")  # Debugging print
        return None

def is_meaningful_filename(filename: str):
    """Check if the filename looks like it has both song and artist info."""
    cleaned_name = os.path.splitext(filename)[0].replace("_", " ").replace("-", " ").replace(".", " ")
    words = cleaned_name.split()
    return len(words) >= 3  # Ensure there's enough detail (e.g., at least "artist song title")

@app.route('/upload-audio/', methods=['POST', 'OPTIONS'])
@cross_origin()
def upload_audio():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Attempt to search Spotify using the filename
        spotify_result = strict_search_spotify_by_filename(file.filename)
        if spotify_result:
            return jsonify(spotify_result)

        # If not found on Spotify, proceed to process the audio file
        # Save the file temporarily
        with NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_file.write(file.read())
            temp_path = temp_file.name

        # Process the file for key detection
        key_info = extract_key_from_audio(temp_path)
        os.remove(temp_path)  # Clean up

        return jsonify(key_info)

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

def strict_search_spotify_by_filename(filename: str):
    """Try to search for the song on Spotify using the filename, with more strict matching."""
    try:
        # Clean and parse the filename to extract artist and track title
        name_without_extension = os.path.splitext(filename)[0]
        cleaned_name = re.sub(r"[_\-\.]", " ", name_without_extension)  # Replace separators with space
        cleaned_name = re.sub(r"\s+", " ", cleaned_name).strip()  # Remove extra spaces
        search_query = cleaned_name.lower()

        # Remove common patterns like track numbers
        search_query = re.sub(r"^\d+\s+", "", search_query)  # Remove leading track numbers
        search_query = re.sub(r"\s+\d+$", "", search_query)  # Remove trailing track numbers

        # Attempt to search Spotify
        results = sp.search(q=search_query, type='track', limit=5)

        if results['tracks']['items']:
            filename_cleaned = re.sub(r"[^a-zA-Z0-9\s]", "", search_query).lower()

            for track in results['tracks']['items']:
                track_name = track['name'].lower()
                artist_name = track['artists'][0]['name'].lower()

                # Verify if both the artist and track name from Spotify match closely with the filename
                if artist_name in filename_cleaned and track_name in filename_cleaned:
                    official_key = get_spotify_official_key(track['external_urls']['spotify'])
                    return {
                        'track_name': track['name'].title(),
                        'artist': track['artists'][0]['name'].title(),
                        'official_key': official_key
                    }
            # If no match found in the results
            return None
        else:
            return None  # No results found, proceed with key detection algorithm
    except Exception as e:
        print(f"Error searching for {filename} on Spotify: {e}")
        return None


class Tonal_Fragment(object):
    def __init__(self, waveform, sr, tstart=None, tend=None):
        self.waveform = waveform
        self.sr = sr
        self.tstart = tstart
        self.tend = tend

        if self.tstart is not None:
            self.tstart = librosa.time_to_samples(self.tstart, sr=self.sr)
        if self.tend is not None:
            self.tend = librosa.time_to_samples(self.tend, sr=self.sr)
        self.y_segment = self.waveform[self.tstart:self.tend]
        self.chromograph = librosa.feature.chroma_cqt(y=self.y_segment, sr=self.sr, bins_per_octave=24)

        self.chroma_vals = []
        for i in range(12):
            self.chroma_vals.append(np.sum(self.chromograph[i]))
        pitches = ['C', 'C#/Db', 'D', 'D#/Eb', 'E', 'F',
                   'F#/Gb', 'G', 'G#/Ab', 'A', 'A#/Bb', 'B']

        self.keyfreqs = {pitches[i]: self.chroma_vals[i] for i in range(12)}

        keys = [pitches[i] + ' major' for i in range(12)] + [pitches[i] + ' minor' for i in range(12)]

        maj_profile = [6.35, 2.23, 3.48, 2.33, 4.38,
                       4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
        min_profile = [6.33, 2.68, 3.52, 5.38, 2.60,
                       3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]

        self.min_key_corrs = []
        self.maj_key_corrs = []
        for i in range(12):
            key_test = [self.keyfreqs.get(pitches[(i + m) % 12]) for m in range(12)]
            self.maj_key_corrs.append(round(np.corrcoef(maj_profile, key_test)[1, 0], 3))
            self.min_key_corrs.append(round(np.corrcoef(min_profile, key_test)[1, 0], 3))

        self.key_dict = {**{keys[i]: self.maj_key_corrs[i] for i in range(12)},
                         **{keys[i + 12]: self.min_key_corrs[i] for i in range(12)}}

        self.key = max(self.key_dict, key=self.key_dict.get)
        self.bestcorr = max(self.key_dict.values())

        self.altkey = None
        self.altbestcorr = None
        for key, corr in self.key_dict.items():
            if corr > self.bestcorr * 0.9 and corr != self.bestcorr:
                self.altkey = key
                self.altbestcorr = corr

    def get_key_info(self):
        key_info = {
            "key": self.key,
            "confidence": self.bestcorr,
            "alternative_key": self.altkey,
            "alternative_confidence": self.altbestcorr
        }
        return key_info

def extract_key_from_audio(audio_path: str):
    """Extract the key from an audio file using the Tonal_Fragment class."""
    y, sr = librosa.load(audio_path, sr=44100, mono=True)
    fragment = Tonal_Fragment(y, sr)
    return fragment.get_key_info()

logging.basicConfig(level=logging.DEBUG)

@app.route('/process-spotify-link/', methods=['POST', 'OPTIONS'])
@cross_origin()
def process_spotify_link():
    try:
        data = request.get_json()
        spotify_url = data.get('spotify_link')

        if not spotify_url:
            return jsonify({"error": "No Spotify link provided"}), 400

        # Get the official key from Spotify
        official_key = get_spotify_official_key(spotify_url)
        
        # Fetch the track details from Spotify
        track_id = spotify_url.split("/")[-1].split("?")[0]
        track = sp.track(track_id)  # Fetch track info
        
        if official_key:
            return jsonify({
                'track_name': track['name'],  # Get the track name
                'artist': track['artists'][0]['name'],  # Get the artist name (first artist)
                'official_key': official_key  # The detected key from the API
            })
        else:
            return jsonify({"error": "Could not retrieve key from Spotify"}), 400

    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
