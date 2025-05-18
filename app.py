import gradio as gr
import boto3
import tempfile
import os
from pydub import AudioSegment
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError

def split_text(text, max_chars=2900):
    """Split text into chunks under max_chars, preferring paragraph or sentence boundaries."""
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

def synthesize_long_text(file_path, voice, access_key, secret_key):
    """Generate MP3 from text file, yielding status updates and error messages."""
    try:
        yield "Starting: Setting up AWS connection...", None
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-west-2'  # Supports neural voices
        )
        polly = session.client('polly')
        
        yield "Reading your text file...", None
        with open(file_path, 'r') as file:
            text = file.read()
        
        if len(text) <= 3000:
            yield "Text is short. Converting to speech now...", None
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice,
                Engine='neural'
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file.write(response['AudioStream'].read())
                output_file = tmp_file.name
            yield "Done! Speech is ready.", output_file
        else:
            yield "Text is long. Breaking it into smaller parts...", None
            chunks = split_text(text)
            num_chunks = len(chunks)
            yield f"Created {num_chunks} parts to process.", None
            audio_files = []
            for i, chunk in enumerate(chunks):
                yield f"Working on part {i+1} of {num_chunks}...", None
                response = polly.synthesize_speech(
                    Text=chunk,
                    OutputFormat='mp3',
                    VoiceId=voice,
                    Engine='neural'
                )
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_file.write(response['AudioStream'].read())
                    audio_files.append(tmp_file.name)
            yield "Combining all audio parts into one file...", None
            combined = AudioSegment.empty()
            for audio_file in audio_files:
                segment = AudioSegment.from_mp3(audio_file)
                combined += segment
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
            combined.export(output_file, format='mp3')
            yield "Finished! Your audio is ready.", output_file
            for audio_file in audio_files:
                os.remove(audio_file)
    except NoCredentialsError:
        yield "Error: AWS credentials are missing. Check your keys.", None
    except PartialCredentialsError:
        yield "Error: AWS keys are incomplete. Please verify.", None
    except ClientError as e:
        yield f"Error: AWS issue - {str(e)}", None
    except FileNotFoundError:
        yield "Error: Couldn’t find your text file.", None
    except Exception as e:
        yield f"Error: Something went wrong - {str(e)}", None

# Voice options (neural-compatible)
voices = ['Joanna', 'Matthew', 'Amy', 'Emma', 'Brian', 'Salli']

# Gradio interface
with gr.Blocks() as app:
    gr.Markdown("# Text-to-Speech with AWS Polly")
    gr.Markdown("Upload a text file and get real-time updates on the process, including any errors.")
    
    with gr.Row():
        file_input = gr.File(label="Upload Text File (.txt)", file_types=['.txt'])
        voice_input = gr.Dropdown(choices=voices, label="Choose Voice", value="Amy")
    
    with gr.Row():
        access_key_input = gr.Textbox(type="password", label="AWS Access Key ID")
        secret_key_input = gr.Textbox(type="password", label="AWS Secret Access Key")
    
    start_button = gr.Button("Generate Audio")
    status_output = gr.Textbox(label="What’s Happening", interactive=False)
    audio_output = gr.Audio(label="Play Audio", interactive=False)
    file_output = gr.File(label="Download Audio", interactive=False)
    
    def start_synthesis(file, voice, access_key, secret_key):
        for status, file_path in synthesize_long_text(file.name, voice, access_key, secret_key):
            if file_path:
                yield status, file_path, file_path
            else:
                yield status, None, None
    
    start_button.click(
        start_synthesis,
        inputs=[file_input, voice_input, access_key_input, secret_key_input],
        outputs=[status_output, audio_output, file_output]
    )

app.launch()