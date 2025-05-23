import gradio as gr
import boto3
import tempfile
import os
import subprocess
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Load environment variables
load_dotenv()

DEFAULT_AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
DEFAULT_AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
DEFAULT_AWS_REGION = os.getenv("AWS_REGION", "us-west-1")

# Split text into chunks under 2900 characters
def split_text(text, max_chars=2900):
    paragraphs = text.split('\n')
    chunks = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
        else:
            sentences = paragraph.split('. ')
            current_chunk = ''
            for sentence in sentences:
                if len(current_chunk) + len(sentence) + 2 <= max_chars:
                    current_chunk += sentence + '. '
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence + '. '
            if current_chunk:
                chunks.append(current_chunk.strip())
    return [chunk for chunk in chunks if chunk]

# Synthesize a single chunk with AWS Polly
def synthesize_chunk(text, voice, polly_client, engine):
    response = polly_client.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId=voice, Engine=engine)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
        tmp.write(response['AudioStream'].read())
        return tmp.name

# Synthesize long text, merging with ffmpeg
def synthesize_long_text(text, voice, access_key, secret_key, region, engine, test_mode=False):
    try:
        if test_mode:
            print("[Test Mode] Received text for synthesis:")
            print(text)
            yield "Test mode: text logged to console.", None
            return

        yield "Connecting to AWS...", None
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        polly = session.client('polly')

        yield "Reading text...", None
        if len(text) <= 3000:
            yield "Synthesizing single chunk...", None
            response = polly.synthesize_speech(Text=text, OutputFormat='mp3', VoiceId=voice, Engine=engine)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp:
                tmp.write(response['AudioStream'].read())
                out_path = tmp.name
            yield "Done!", out_path
        else:
            yield "Splitting into smaller parts...", None
            chunks = split_text(text)
            yield f"Synthesizing {len(chunks)} chunks in parallel...", None
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(synthesize_chunk, chunk, voice, polly, engine) for chunk in chunks]
                paths = [future.result() for future in futures]

            yield "Merging audio chunks...", None
            with open('filelist.txt', 'w') as f:
                for p in paths:
                    f.write(f"file '{p}'\n")
            out_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
            subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'filelist.txt', '-c', 'copy', out_path], check=True)
            os.remove('filelist.txt')
            for p in paths:
                os.remove(p)
            yield "Done!", out_path
    except NoCredentialsError:
        yield "Error: Missing AWS credentials.", None
    except PartialCredentialsError:
        yield "Error: Incomplete AWS credentials.", None
    except ClientError as e:
        msg = e.response.get('Error', {}).get('Message', str(e))
        yield f"AWS Error: {msg}", None
    except subprocess.CalledProcessError:
        yield "Error: FFmpeg failed to merge audio chunks. Ensure FFmpeg is installed.", None
    except Exception as e:
        yield f"Error: {str(e)}", None

# Load file content into textbox
def load_file(file_obj):
    if not file_obj:
        return ""
    try:
        with open(file_obj.name, 'r', encoding='utf-8') as f:
            content = f.read().replace('\n', ' ').strip()
            return content
    except Exception as e:
        print(f"Error loading file: {e}")
        return ''

# Voice and engine options
voices = ['Joanna', 'Matthew', 'Amy', 'Emma', 'Brian', 'Salli']
engines = ['standard', 'neural']

# Gradio interface
with gr.Blocks(title="AWS Polly Text-to-Speech App") as app:
    gr.Markdown("## AWS Polly Text-to-Speech Generator")
    gr.Markdown("Synthesize text using AWS Polly or use Test Mode to log text to the console.")

    with gr.Accordion("AWS Credentials", open=False):
        with gr.Row():
            test_toggle = gr.Checkbox(label="Test Mode (no AWS)", value=True)
            access_key_input = gr.Textbox(type="password", label="AWS Access Key ID", value=DEFAULT_AWS_ACCESS_KEY or "")
            secret_key_input = gr.Textbox(type="password", label="AWS Secret Access Key", value=DEFAULT_AWS_SECRET_KEY or "")
            region_input = gr.Textbox(label="AWS Region", value=DEFAULT_AWS_REGION)
        if not DEFAULT_AWS_ACCESS_KEY or not DEFAULT_AWS_SECRET_KEY:
            gr.Markdown("**Warning:** AWS credentials are not set. Please enter them below.")
        else:
            gr.Markdown("**Note:** AWS credentials are loaded from environment variables.")

    with gr.Row():
        file_input = gr.File(label="Upload .txt File", file_types=['.txt'])
        with gr.Column():
            voice_input = gr.Dropdown(choices=voices, label="Voice", value="Amy")
            engine_input = gr.Dropdown(choices=engines, label="Engine", value="neural")

    with gr.Row():
        text_input = gr.Textbox(label="Text for Synthesis", lines=10)
    file_input.change(load_file, inputs=file_input, outputs=text_input)

    start_button = gr.Button("Start Synthesis")
    status_output = gr.Textbox(label="Status", interactive=False)
    audio_output = gr.Audio(label="Play Audio")
    file_output = gr.File(label="Download MP3")

    def run_process(file_obj, text, voice, ak, sk, region, engine, test_mode):
        content = text or (open(file_obj.name).read() if file_obj else '')
        for status, path in synthesize_long_text(content, voice, ak, sk, region, engine, test_mode):
            if path:
                yield status, path, path
            else:
                yield status, None, None

    start_button.click(
        run_process,
        inputs=[file_input, text_input, voice_input, access_key_input, secret_key_input, region_input, engine_input, test_toggle],
        outputs=[status_output, audio_output, file_output]
    )

if __name__ == "__main__":
    app.launch()