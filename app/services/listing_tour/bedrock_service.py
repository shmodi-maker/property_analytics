"""
ListingTour Bedrock Service

This module handles prompt loading and communication with AWS Bedrock
for generating AI summaries for ListingTour pages.
"""

import os
from pathlib import Path

import boto3


class BedrockService:

    def __init__(self):
        """
        Initialize the Bedrock Runtime client.
        """

        self.region = os.getenv(
            "AWS_REGION",
            "us-east-1",
        )

        self.model_id = os.getenv(
            "BEDROCK_MODEL_ID",
            "amazon.nova-micro-v1:0",
        )

        self.client = boto3.client(
            "bedrock-runtime",
            region_name=self.region,
        )

    def load_prompt(
        self,
        prompt_name: str,
    ) -> str:
        """
        Load a ListingTour prompt from the prompts directory.
        """

        project_root = Path(__file__).resolve().parents[3]

        prompt_path = (
            project_root
            / "ListingTour"
            / "property_discovery"
            / "prompts"
            / prompt_name
        )

        if not prompt_path.exists():
            raise FileNotFoundError(
                f"Prompt file not found: {prompt_path}"
            )

        return prompt_path.read_text(
            encoding="utf-8"
        )

    def generate_summary(
        self,
        prompt: str,
    ) -> str:
        """
        Send a prompt to Bedrock and return the generated response.
        """

        response = self.client.converse(
            modelId=self.model_id,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt,
                        }
                    ],
                }
            ],
            inferenceConfig={
                "temperature": 0.2,
                "maxTokens": 500,
            },
        )

        return (
            response["output"]["message"]["content"][0]["text"]
        )