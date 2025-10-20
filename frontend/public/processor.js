class AudioProcessor extends AudioWorkletProcessor {
  constructor(options) {
    super();
    
    // Configuration
    this.sampleRate = options.processorOptions.sampleRate || 16000;
    this.timeSlice = options.processorOptions.timeSlice || 250;
    this.numberOfChannels = options.processorOptions.numberOfChannels || 1;
    this.bufferSize = options.processorOptions.bufferSize || 2048;
    
    // Calculate chunk size based on timeSlice
    this.chunkSize = Math.floor((this.timeSlice * this.sampleRate) / 1000);
    
    // Initialize buffer
    this.buffer = new Float32Array(this.chunkSize);
    this.bufferIndex = 0;
    
    // Debug info
    console.log(`AudioProcessor initialized:
      Sample Rate: ${this.sampleRate}Hz
      Time Slice: ${this.timeSlice}ms
      Chunk Size: ${this.chunkSize} samples
      Buffer Size: ${this.bufferSize} samples
      Channels: ${this.numberOfChannels}
      Expected output size: ${this.chunkSize * 2} bytes`);
  }

  process(inputs, outputs) {
    const input = inputs[0];
    if (!input || input.length === 0) return true;
    
    const channel = input[0];
    
    for (let i = 0; i < channel.length; i++) {
      if (this.bufferIndex < this.chunkSize) {
        this.buffer[this.bufferIndex++] = channel[i];
      }
      
      if (this.bufferIndex >= this.chunkSize) {
        // Send buffer when full
        this.port.postMessage(this.buffer.slice());
        
        // Reset buffer
        this.buffer = new Float32Array(this.chunkSize);
        this.bufferIndex = 0;
      }
    }
    
    return true;
  }
}

registerProcessor('processor', AudioProcessor);