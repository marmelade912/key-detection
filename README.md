# Key Detection Web App

This project is a web application for detecting the musical key of an audio file or a Spotify track using the Spotify API. The application provides an option to upload an audio file or input a Spotify link to fetch the official key from Spotify.

## Features

- **Upload Audio File**: Upload `.wav`, `.mp3`, or other audio formats for key detection.
- **Spotify Integration**: Enter a Spotify link to fetch the official key directly from the Spotify API.
- **Key Detection**: Uses chroma features to detect the musical key of the audio.
- **Confidence Scores**: Provides a confidence level for both the detected key and an alternative key if applicable.

## Getting Started

### Prerequisites

Ensure you have the following installed:

- **Python 3.8+**
- **Node.js** (for the frontend)
- **ngrok** (or your preferred tunneling tool for local development)
- **Spotify API Credentials**: You need a `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` from the Spotify Developer Dashboard.

### Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/marmelade912/key-detection.git
    cd key-detection
    ```

2. Create a virtual environment and activate it:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

4. Set up your `.env` file in the root directory:

    ```plaintext
    SPOTIPY_CLIENT_ID=your_spotify_client_id
    SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
    ```

5. Run the Flask backend:

    ```bash
    python app.py
    ```

6. Navigate to the frontend directory and install dependencies:

    ```bash
    cd frontend
    npm install
    ```

7. Run the Next.js frontend:

    ```bash
    npm run dev
    ```

8. Use **ngrok** or another tunneling service to expose your Flask backend. Example:

    ```bash
    ngrok http 5000
    ```

    Update the `apiUrl` in your frontend to match the ngrok URL.

### Usage

Once both the backend and frontend are running, you can:

1. Open the web app in your browser.
2. Either paste a Spotify link into the input box or upload an audio file.
3. Click "Detect Key" and see the detected key along with any confidence scores.

### API Endpoints

- **POST `/process-spotify-link/`**: Process a Spotify link and return the detected key from the Spotify API.
- **POST `/upload-audio/`**: Upload an audio file and detect the musical key using `librosa` and chroma features.

### Example Response

```json
{
  "track_name": "Track Title",
  "artist": "Artist Name",
  "official_key": "C Major",
  "confidence": 0.97,
  "alternative_key": "A Minor",
  "alternative_confidence": 0.92
}
