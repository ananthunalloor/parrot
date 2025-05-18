# AWS Polly Text-to-Speech Gradio App

This Gradio-based application allows you to convert large text (e.g., podcasts, books) into MP3 audio using AWS Polly. It supports chunking long text, neural voices, environment-based credential loading, test modes, error handling, and automatic download of the generated MP3.

## Features

- **Long Text Chunking**: Automatically splits text into AWS-compatible chunks if over 3000 characters.
- **AWS Credential Management**: Loads from `.env` or UI overrides (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION).
- **Test Mode**: Toggle to log text to the console instead of calling AWS.
- **Chunk Test**: Preview how input text will be split before synthesis.
- **Neural Voices**: Select from Amy, Joanna, Matthew, Emma, Brian, Salli.

## Prerequisites

- Python 3.8 or newer
- AWS account with Polly permissions (if not using Test Mode)
- `ffmpeg` installed and available on your system PATH for audio merging

## Getting Started

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Create and activate a virtual environment**

   ```bash
   py -m venv .venv

   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure AWS credentials**

   - Create a `.env` file in the project root with:

     ```dotenv
     AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
     AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
     AWS_REGION=us-west-2
     ```

   - Or leave `.env` empty and enter keys in the UI accordion.

5. **Run the app**

   ```bash
   python app.py
   ```

   or

   - **Shell (macOS/Linux or WSL)**: `./start.sh`
   - **Batch (Windows)**: `start.bat`

   The Gradio interface will launch in your browser (typically at `http://127.0.0.1:7860`).

## Helper Scripts

Four helper scripts to streamline setup and startup:

- **install.sh** / **install.bat**: Create & activate the virtual environment and install dependencies.
- **start.sh** / **start.bat**: Activate the environment and launch the app.

Simply make these scripts executable (for shell) or run the batch files on Windows to get started quickly.

## Usage

1. **Upload** a `.txt` file or paste/edit text in the editor.
2. **Test Chunking** to preview how the text will be split.
3. **Select** a voice and optionally enable **Test Mode**.
4. **Start Synthesis** and watch the status updates.
5. **Listen** to the audio in the player or download the MP3.

## Troubleshooting

- **Missing credentials**: Ensure `.env` is correctly populated or enter keys in UI.
- **FFmpeg errors**: Install FFmpeg from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to PATH.
- **Chunking issues**: Adjust `max_chars` in `split_text` or simplify input text.

## License

This project is released under the MIT License.
