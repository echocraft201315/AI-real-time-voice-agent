import asyncio
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions
)
from fastapi.websockets import WebSocket
import numpy as np
from config.logging import get_logger

logger = get_logger(__name__)

class DeepgramTranscriber:
    def __init__(self, api_key, websocket: WebSocket):
        self.api_key = api_key
        self.is_finals = []
        self.dg_connection = None
        self.config = DeepgramClientOptions(options={"keepalive": "true"})
        # Create and initialize transcriber
        self.deepgram = DeepgramClient(self.api_key, self.config)
        self.transcription_complete = False
        self.websocket = websocket
        
    async def initialize(self):
        """ Initialize the Deepgram client and set up event handlers """
        self.dg_connection = self.deepgram.listen.asyncwebsocket.v("1")
        self._setup_event_handlers()
        await self._start()
        
    def _setup_event_handlers(self):
        """ Set up all the event handlers for the Deepgram connection """
        self.dg_connection.on(LiveTranscriptionEvents.Open, self.on_open)
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, self.on_message)
        self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self.on_speech_started)
        #When speech pauses long enough, utterance end is triggered
        # self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self.on_utterance_end)
        self.dg_connection.on(LiveTranscriptionEvents.Close, self.on_close)
        self.dg_connection.on(LiveTranscriptionEvents.Error, self.on_error)
        # Unexpected messages may be received 
        self.dg_connection.on(LiveTranscriptionEvents.Unhandled, self.on_unhandled)
        
    async def _start(self):
        """Start the transcription service"""
        options = LiveOptions(
            model="nova-2",
            language="en-IN",
            smart_format=True,
            encoding="linear16",
            channels=1,
            sample_rate=16000,
            interim_results=True,
            utterance_end_ms="1000",
            vad_events=True,
            endpointing=300,
        )
            
        addons = {"no_delay": "true"}
            
        print("\n\nStart talking! Press Ctrl+C to stop...\n")
        
        if await self.dg_connection.start(options, addons=addons) is False:
            print("Failed to connect to Deepgram")
            return False
            
        return True
        
            
    async def cleanup(self):
        """Clean up resources"""
        if self.dg_connection:
            await self.dg_connection.finish()
        print("Finished")

    async def transcribe(self, audio_array: np.ndarray):
        try:
            if not self.dg_connection:
                await self.initialize()
            
            await self.dg_connection.send(audio_array.tobytes())
            await asyncio.sleep(0.05)
            # return self.transcriptions
            
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise  
        
    async def reset(self):
        self.is_finals = []
        self.transcription_complete = False

    # Event Handlers
    """ 
    self: the class instance (automatically provided by Python)
    _self: the event handler itself (provided by Deepgram)
    """
    async def on_open(self, *args, **kwargs):
        print("Connection Open")
        await self.websocket.send_json({"type": "deepgram_connection_open"})
        
        
    async def on_message(self, _self, result, **kwargs):
        sentence = result.channel.alternatives[0].transcript
        if len(sentence) == 0:
            return
            
        if result.is_final:
            self.is_finals.append(sentence)
            if result.speech_final:
                utterance = " ".join(self.is_finals)
                print(f"Speech Final: {utterance}")
                self.transcription_complete = True
            else:
                print(f"Is Final: {sentence}")
        else:
            print(f"Interim Results: {sentence}")
        
    async def on_speech_started(self, *args, **kwargs):
        print("Speech Started")
        
    async def on_utterance_end(self, *args, **kwargs):
        print("Utterance End")
        if len(self.is_finals) > 0:
            utterance = " ".join(self.is_finals)
            # await self.response_generator.process_response(utterance,self.client_id)
            print(f"Utterance End: {utterance}")
            self.transcription_complete = True
            
    async def on_close(self, *args, **kwargs):
        print("Connection Closed")
        
    async def on_error(self, _self, error, **kwargs):
        print(f"Handled Error: {error}")
        await self.websocket.send_json({"type": "deepgram_connection_closed"})
        
    async def on_unhandled(self, _self, unhandled, **kwargs):
        print(f"Unhandled Websocket Message: {unhandled}")
