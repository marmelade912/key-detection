import { useState, useRef } from 'react';

export default function Home() {
  const [spotifyLink, setSpotifyLink] = useState('');
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (spotifyLink && file) {
      alert('Please provide either a Spotify link or upload a file.');
      return;
    }

    const apiUrl = 'https://6985-76-145-177-181.ngrok-free.app'; // Point to your backend port

    if (spotifyLink) {
      // Process Spotify link
      try {
        console.log("Sending Spotify link to backend:", spotifyLink);
        const response = await fetch(`${apiUrl}/process-spotify-link/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ spotify_link: spotifyLink }),
        });

        if (!response.ok) {
          throw new Error(`Failed with status ${response.status}`);
        }

        const data = await response.json();
        console.log("Received data from backend:", data);
        setResult(data);
      } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while processing the Spotify link.');
      }
    } else if (file) {
      // Process file upload
      const formData = new FormData();
      formData.append('file', file);

      try {
        console.log("Uploading file to backend:", file.name);
        const response = await fetch(`${apiUrl}/upload-audio/`, {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Failed with status ${response.status}`);
        }

        const data = await response.json();
        console.log("Received data from backend:", data);
        setResult(data);
      } catch (error) {
        console.error('Error:', error);
        alert('An error occurred while uploading the file.');
      }
    } else {
      alert('Please provide a Spotify link or upload an audio file.');
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Key Detection</h1>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: '10px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>Spotify Link:</label>
          <input
            type="text"
            value={spotifyLink}
            onChange={(e) => setSpotifyLink(e.target.value)}
            style={{ width: '300px', padding: '5px' }}
          />
        </div>
        <div style={{ marginBottom: '10px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>Or Upload Audio File:</label>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <input
              type="file"
              accept="audio/*"
              ref={fileInputRef}
              onChange={(e) => setFile(e.target.files[0])}
            />
            {file && (
              <button
                type="button"
                onClick={() => {
                  setFile(null);
                  fileInputRef.current.value = null;
                }}
                style={{
                  marginLeft: '10px',
                  padding: '5px 10px',
                  cursor: 'pointer',
                }}
              >
                X
              </button>
            )}
          </div>
        </div>
        <button type="submit" style={{ padding: '10px 20px' }}>Detect Key</button>
      </form>

      {result && (
        <div style={{ marginTop: '20px' }}>
          <h2>Result:</h2>
          <p><strong>Track Name:</strong> {result.track_name || 'N/A'}</p>
          <p><strong>Artist:</strong> {result.artist || 'N/A'}</p>
          <p><strong>Official Key:</strong> {result.official_key || result.key}</p>
          {result.confidence && <p><strong>Confidence:</strong> {result.confidence}</p>}
          {result.alternative_key && (
            <p>
              <strong>Alternative Key:</strong> {result.alternative_key} (Confidence: {result.alternative_confidence})
            </p>
          )}
          {result.error && <p><strong>Error:</strong> {result.error}</p>}
        </div>
      )}
    </div>
  );
}
