import gradio as gr
import boto3
import tempfile
import os
from pydub import AudioSegment

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
    """Generate MP3 from text file using provided AWS credentials, yielding status updates and final file path."""
    try:
        # Initialize AWS session and Polly client with user-provided credentials
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name='us-east-1'  # Ensure this region supports neural voices
        )
        polly = session.client('polly', region_name='us-east-1')
        
        # Read the text file
        with open(file_path, 'r') as file:
            text = file.read()
        
        if len(text) <= 3000:
            # Synthesize short text directly
            response = polly.synthesize_speech(
                Text=text,
                OutputFormat='mp3',
                VoiceId=voice,
                Engine='neural'  # Use neural engine for high-quality output
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tmp_file.write(response['AudioStream'].read())
                output_file = tmp_file.name
            yield "Synthesis completed!", output_file
        else:
            # Handle long text by splitting into chunks
            chunks = split_text(text)
            num_chunks = len(chunks)
            yield f"Splitting text into {num_chunks} chunks.", None
            audio_files = []
            for i, chunk in enumerate(chunks):
                yield f"Synthesizing chunk {i+1} of {num_chunks}...", None
                response = polly.synthesize_speech(
                    Text=chunk,
                    OutputFormat='mp3',
                    VoiceId=voice,
                    Engine='neural'  # Apply neural engine to each chunk
                )
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                    tmp_file.write(response['AudioStream'].read())
                    audio_files.append(tmp_file.name)
            yield "Concatenating audio files...", None
            combined = AudioSegment.empty()
            for audio_file in audio_files:
                segment = AudioSegment.from_mp3(audio_file)
                combined += segment
            output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
            combined.export(output_file, format='mp3')
            yield "Synthesis completed!", output_file
            # Clean up temporary chunk files
            for audio_file in audio_files:
                os.remove(audio_file)
    except Exception as e:
        yield f"Error: {str(e)}", None  # Handle credential or synthesis errors

# Define voice options, including "Amy" (all neural-compatible)
voices = ['Joanna', 'Matthew', 'Amy', 'Emma', 'Brian', 'Salli']

# Build the Gradio interface
with gr.Blocks() as app:
    gr.Markdown("# Text-to-Speech with AWS Polly (Neural Engine)")
    gr.Markdown("Convert text files into high-quality speech using AWS Polly's neural engine.")
    
    # Input section for text file and voice selection
    with gr.Row():
        file_input = gr.File(label="Upload Text File (.txt)", file_types=['.txt'])
        voice_input = gr.Dropdown(choices=voices, label="Select Voice", value="Amy")  # Default to Amy
    
    # Section to configure AWS keys
    with gr.Row():
        access_key_input = gr.Textbox(type="password", label="AWS Access Key ID")
        secret_key_input = gr.Textbox(type="password", label="AWS Secret Access Key")
    
    # Controls and outputs
    start_button = gr.Button("Start Synthesis")
    status_output = gr.Textbox(label="Status", interactive=False)
    audio_output = gr.Audio(label="Listen", interactive=False)
    file_output = gr.File(label="Download MP3", interactive=False)
    
    def start_synthesis(file, voice, access_key, secret_key):
        """Process inputs and yield status, audio, and file outputs."""
        for status, file_path in synthesize_long_text(file.name, voice, access_key, secret_key):
            if file_path:
                yield status, file_path, file_path
            else:
                yield status, None, None
    
    # Connect button to synthesis function
    start_button.click(
        start_synthesis,
        inputs=[file_input, voice_input, access_key_input, secret_key_input],
        outputs=[status_output, audio_output, file_output]
    )

# Launch the application
app.launch()