export interface VoiceConfig {
    sampleRate?: number;
    silenceTimeout?: number;
    chunkSize?: number;
    onAudioData?: (data: Blob) => void;
  }