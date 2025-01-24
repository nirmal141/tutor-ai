import requests

class LocalLLM:
    def __init__(self, device="CPU"):
        self.device = device
        self.api_base = "http://127.0.0.1:1234"
        self.timeout = 60

    def generate(self, prompt, max_length=2048, additional_context=None, teaching_style=None):
        try:
            # Test connection before making the actual request
            requests.get(self.api_base, timeout=2)  # Quick connection test
        except requests.exceptions.ConnectionError:
            raise Exception(
                "Cannot connect to LLM server. Please ensure the local LLM server is running "
                f"at {self.api_base} and try again."
            )
            
        # Add teaching style context
        if teaching_style:
            prompt = f"Focus on {teaching_style} learning style. {prompt}"
            
        # Add curriculum context if provided
        if additional_context:
            prompt = f"Using this curriculum context:\n{additional_context}\n\n{prompt}"
            
        try:
            response = requests.post(
                f"{self.api_base}/v1/chat/completions",
                json={
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7,
                    "max_tokens": max_length,
                    "stream": True
                },
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                return response.iter_lines()
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
