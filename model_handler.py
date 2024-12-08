import requests
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
import streamlit as st

class LocalLLM:
    def __init__(self, device="NPU"):
        self.device = device
        self.api_base = "http://127.0.0.1:1234"
        self.providers = ['NPUExecutionProvider'] if self.device == "NPU" else ['CPUExecutionProvider'] 
        self.timeout = 60

    def generate(self, prompt, max_length=2048, additional_context=None, teaching_style=None):
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
                    "stream": True  # Enable streaming
                },
                timeout=self.timeout,
                stream=True  # Enable streaming for requests
            )
            
            if response.status_code == 200:
                # Return the response iterator
                return response.iter_lines()
            else:
                raise Exception(f"Error: {response.status_code}, {response.text}")
            
        except requests.exceptions.Timeout:
            raise Exception("Request timed out. Please try again.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
