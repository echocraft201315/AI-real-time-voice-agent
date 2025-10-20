import { useState, useRef, useEffect } from "react";
import { TbMicrophone } from "react-icons/tb";
import { FaStopCircle, FaMicrophone, FaMicrophoneSlash } from "react-icons/fa";
import BlobAnimation from "./components/AiAnimation";
import { useVoiceRecorder } from "./hooks/useVoiceRecorder";
import { useWebSocket } from "./hooks/useWebSocket";

function App() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [websocketReady, setWebsocketReady] = useState(false);
  const [streamError, setStreamError] = useState('');
  const [isMuted, setIsMuted] = useState(false);
  const [isFirstAudioChunkReceived, setFirstAudioChunkReceived] = useState(false);
  const [responseTime, setResponseTime] = useState(0);
  
  const audioContextRef = useRef<AudioContext | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const audioBufferSourceRef = useRef<AudioBufferSourceNode | null>(null);
  const audioQueueRef = useRef<ArrayBuffer[]>([]);
  const isProcessingRef = useRef(false);

  // Initialize AudioContext lazily
  const getAudioContext = () => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
      // Create gain node for muting
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
    }
    return audioContextRef.current;
  };


  const { error: socketError, connect, disconnect, sendMessage } = useWebSocket({
    url: `ws://localhost:8000/ws/audio/${Date.now()}`,
    onOpen: () => console.log("Connected!"),
    onMessage: handleWebSocketMessage,
    onError: (error) => {
      console.error("WebSocket error:", error);
      setStreamError("Connection error occurred");
    },
    onClose: () => console.log("Disconnected!")
  });

  const { error: recorderError, startRecording, stopRecording } = useVoiceRecorder({
    onAudioData: (data) => {
      data.arrayBuffer().then(buffer => {
        try {
          // if(!isMuted){
            const audioData = new Uint8Array(buffer);
            sendMessage(audioData);
          // }
        } catch (err) {
          console.error('Error sending audio data:', err);
          setStreamError('Failed to send audio data');
        }
      });
    }
  });

  const playNextChunk = async () => {
    if (isProcessingRef.current || audioQueueRef.current.length === 0) {
      return;
    }

    isProcessingRef.current = true;
    setIsPlaying(true);

    try {
      const ctx = getAudioContext();
      const chunk = audioQueueRef.current.shift()!;
      
      // Stop any currently playing audio
      if (audioBufferSourceRef.current) {
        try {
          audioBufferSourceRef.current.stop();
        } catch (e) {
          // Ignore stop errors
        }
      }

      const audioBuffer = await ctx.decodeAudioData(chunk.slice(0));
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      
      // Connect to gain node instead of destination
      source.connect(gainNodeRef.current!);
      
      audioBufferSourceRef.current = source;

      source.onended = () => {
        isProcessingRef.current = false;
        audioBufferSourceRef.current = null;
        
        if (audioQueueRef.current.length > 0) {
           playNextChunk()
        } else {
          setIsPlaying(false);
        }
      };

      await ctx.resume();
      // Set initial gain based on mute state
      gainNodeRef.current!.gain.value = isMuted ? 0 : 1;
      source.start(0);
    } catch (err) {
      console.error("Error playing audio chunk:", err);
      isProcessingRef.current = false;
      setIsPlaying(false);
      setStreamError('Failed to play audio chunk');
      
      if (audioQueueRef.current.length > 0) {
         playNextChunk()
      }
    }
  };

  async function handleWebSocketMessage(message: string) {
    try {
      const data = JSON.parse(message);
      if(data.type === 'deepgram_connection_open') {
        setWebsocketReady(true)
      }else if(data.type === 'response_generation_start') {
        console.log("User: ",data.text)
        window.responseStartTime = Date.now();
      }else if(data.type === 'audio_stream_start') {
        console.log("AI Assistant: ",data.text)
      }else if (data.type === 'audio_chunk') {
        // Convert base64 to ArrayBuffer

        if(!isFirstAudioChunkReceived){
          const duration = Date.now() - window.responseStartTime;
          setFirstAudioChunkReceived(true);
          setResponseTime(duration)
          window.responseStartTime = Date.now();
        }

        const binary = atob(data.data);
        const buffer = new ArrayBuffer(binary.length);
        const bytes = new Uint8Array(buffer);
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i);
        }

        // Add to queue
        audioQueueRef.current.push(buffer);

        // Start playing if not already processing
        if (!isProcessingRef.current) {
          playNextChunk();
        }
      } else if (data.type === 'audio_stream_end') {
        if(data.remaining_sentence_chunk_count === 0){
          setFirstAudioChunkReceived(false)
          console.log("Reset received chunk flag")
        }
        console.log("Audio stream complete");
      } else if (data.type === 'audio_stream_error') {
        console.error("Stream error:", data.error);
        setStreamError(data.error);
      }
    } catch (err) {
      console.error("Error processing WebSocket message:", err);
    }
  }

  const handleStartRecording = async () => {
    try {
      const ctx = getAudioContext();
      await ctx.resume();
      
      setStreamError('');
      audioQueueRef.current = [];
      isProcessingRef.current = false;
      
      if (audioBufferSourceRef.current) {
        try {
          audioBufferSourceRef.current.stop();
        } catch (e) {
          // Ignore stop errors
        }
      }
      
      connect();
      startRecording();
      setIsRecording(true);
    } catch (err) {
      console.error('Error starting recording:', err);
      setStreamError('Failed to start recording');
    }
  };

  const handleStopRecording = () => {
    stopRecording();
    disconnect();
    setIsRecording(false);
    setWebsocketReady(false);
    setIsPlaying(false);
    setIsMuted(false);
    setFirstAudioChunkReceived(false);
    setStreamError('');
    setResponseTime(0);
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (audioBufferSourceRef.current) {
        try {
          audioBufferSourceRef.current.stop();
        } catch (e) {
          // Ignore stop errors
        }
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);


  const toggleMute = () => {
    if(isMuted){
      startRecording();
    }else{
      stopRecording();
    }
    setIsMuted(!isMuted);
  };

  return (
    <div className="container">
      <div className="content">
        <h1>Open Source Voice AI for developers</h1>

        <p className="subtitle">
          Create voice agents your way. An open-source framework letting you
          plug in any LLM, TTS, or STT model to build the perfect voice AI
          solution.
        </p>

        {isRecording ? (
          <BlobAnimation
            primaryColor="#6ee7b7"
            backgroundColor="#242424"
            size="20vh"
          />
        ) : (
          <div className="mic-container">
            <button
              className="mic-button"
              aria-label="Activate voice input"
              onClick={handleStartRecording}
              disabled={isPlaying}
            >
              <TbMicrophone className="mic-icon" />
            </button>
          </div>
        )}

        <p>{responseTime>0?`${responseTime}ms`:""}</p>
        <button className="cta-message">
          {isRecording ? 
          isMuted?"Microphone is muted":
          isPlaying?"I'm speaking...":
          !websocketReady?"Wait a second...": "I'm listening..." : "hit record! 🎯"}
        </button>
        
        {streamError && (
          <div className="text-red-500">
            {streamError}
          </div>
        )}

        {recorderError && (
          <p className="text-red-500">
            {recorderError}
          </p>
        )}
        
        {socketError && (
          <p className="text-red-500">
            {socketError}
          </p>
        )}

        {isRecording && (
          <>
          <button
            className="stop-button"
            onClick={handleStopRecording}
          >
            <FaStopCircle />
          </button>


          <button
            className="stop-button"
            onClick={toggleMute}
          >
            {isMuted ? (
              <FaMicrophoneSlash  />
            ) : (
              <FaMicrophone  />
            )}
          </button>

          </>

        )}
      </div>
    </div>
  );
}

export default App;