import requests
from youtube_transcript_api import YouTubeTranscriptApi

def fetch_youtube_videos(api_key, query):
    """Fetch YouTube videos based on a search query."""
    url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&key={api_key}&maxResults=5"
    response = requests.get(url)
    
    # Check if the response is successful
    if response.status_code == 200:
        try:
            return response.json().get('items', [])
        except ValueError as e:
            print(f"Error decoding JSON: {str(e)}")
            print("Response text:", response.text)  # Print the response text for debugging
            return []
    else:
        print(f"Error fetching videos: {response.status_code}")
        print("Response text:", response.text)  # Print the response text for debugging
        return []

def fetch_video_transcript(video_id):
    """Fetch transcript of a video by its ID."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except Exception as e:
        print(f"Error fetching transcript for video {video_id}: {str(e)}")
        return None

# Example usage
if __name__ == "__main__":
    api_key = 'AIzaSyDwC4L7KV83avQVAshiAHeJGHfJUZuy9wM'  # Replace with your YouTube Data API key
    query = "Yann LeCun"
    
    # Fetch videos
    videos = fetch_youtube_videos(api_key, query)
    
    # Initialize a variable to hold all transcripts
    combined_transcripts = ""

    for video in videos:
        video_id = video['id']['videoId']
        transcript = fetch_video_transcript(video_id)
        if transcript:
            combined_transcripts += f"Transcript for '{video['snippet']['title']}':\n{transcript}\n\n"

    # Print the combined transcripts
    print("Combined Transcripts:\n")
    print(combined_transcripts)