AI4Bharat: Court Judgment Action Plan Pipeline ⚖️
An Intelligent System for Transforming Legal Documentation into Actionable Insights

This project provides an automated, end-to-end pipeline designed to process complex Indian court judgments. By leveraging Computer Vision for document optimization and Generative AI for legal reasoning, the system converts dense legal text into verified action plans.

🏗️ System Architecture
The following diagram illustrates the event-driven workflow from document ingestion to the final AI-generated action plan.

📂 Project Documentation
For a deep dive into the engineering and logic behind this solution, please refer to the following documents:

📋 Project Requirements: Detailed EARS-format requirements covering OCR accuracy, data privacy, and system reliability.

🏗️ Technical Design: Technical breakdown of the OpenCV preprocessing, AWS Textract extraction, and Amazon Bedrock (Claude 3) logic.

🚀 Key Features
Intelligent Preprocessing: Auto-enhances scanned documents to 300 DPI using OpenCV to ensure maximum OCR accuracy.

Legal Entity Extraction: Utilizes AWS Textract to identify key dates, parties, and legal statutes from semi-structured data.

AI Action Engine: Employs Amazon Bedrock to synthesize judgments into a step-by-step verified action plan.

Robust Audit Trail: Built with a "Security-First" approach, logging all transformations for transparency in governance.

🛠️ Tech Stack
Language: Python

Computer Vision: OpenCV, MediaPipe

Cloud Infrastructure: AWS (S3, Lambda, Textract, DynamoDB)

AI/LLM: Amazon Bedrock (Claude 3)

Interface: Streamlit (for the AI-Powered Image Optimizer)
