import React, { useState, useRef, useEffect, useCallback } from 'react';
import './VoiceAssistant.css';

// Extend the Window interface to include SpeechRecognition
declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

interface VoiceAssistantProps {
  onVoiceInput: (text: string, audioBlob?: Blob) => void;
  isLoading?: boolean;
  disabled?: boolean;
}

const VoiceAssistant: React.FC<VoiceAssistantProps> = ({ onVoiceInput, isLoading = false, disabled = false }) => {
  const [isListening, setIsListening] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [permissionStatus, setPermissionStatus] = useState<'unknown' | 'granted' | 'denied' | 'requesting'>('unknown');
  const [deviceStatus, setDeviceStatus] = useState<'unknown' | 'available' | 'not-found'>('unknown');
  const [errorMessage, setErrorMessage] = useState<string>('');
  
  const recognitionRef = useRef<any>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  // Check for available microphone devices
  const checkMicrophoneDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioDevices = devices.filter(device => device.kind === 'audioinput');
      
      if (audioDevices.length === 0) {
        setDeviceStatus('not-found');
        setErrorMessage('No microphone devices found. Please connect a microphone.');
        return false;
      }
      
      setDeviceStatus('available');
      setErrorMessage('');
      return true;
    } catch (error) {
      console.warn('Could not enumerate devices:', error);
      setDeviceStatus('unknown');
      return true; // Assume devices are available if we can't check
    }
  };

  // Check microphone permissions
  const checkMicrophonePermission = async () => {
    try {
      if (!navigator.permissions) {
        // Fallback for browsers that don't support permissions API
        return 'unknown';
      }
      
      const permission = await navigator.permissions.query({ name: 'microphone' as PermissionName });
      return permission.state;
    } catch (error) {
      console.warn('Could not check microphone permissions:', error);
      return 'unknown';
    }
  };

  // Silence timer for auto-stop after silence
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);

// Start listening: get mic, start media recorder, start speech recognition
const startListening = useCallback(async () => {
  try {
    setErrorMessage('');
    setTranscript('');
    setConfidence(0);
    // Check for devices
    const devicesAvailable = await checkMicrophoneDevices();
    if (!devicesAvailable) return;
    // Check permission
    let permission = permissionStatus;
    if (permission === 'unknown') {
      const permResult = await checkMicrophonePermission();
      // Map 'prompt' to 'unknown' for our state
      let mappedPerm: 'unknown' | 'granted' | 'denied' | 'requesting';
      if (permResult === 'granted' || permResult === 'denied') {
        mappedPerm = permResult;
      } else {
        mappedPerm = 'unknown';
      }
      permission = mappedPerm;
      setPermissionStatus(mappedPerm);
    }
    if (permission === 'denied') {
      setErrorMessage('Microphone access denied. Please grant permission and try again.');
      return;
    }
    // Get user media
    const stream = await navigator.mediaDevices.getUserMedia({ audio: { autoGainControl: true } });
    // Setup media recorder
    const mediaRecorder = new MediaRecorder(stream);
    chunksRef.current = [];
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };
    mediaRecorder.onstop = () => {
      const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
      setAudioBlob(blob);
      stream.getTracks().forEach(track => track.stop());
    };
    mediaRecorderRef.current = mediaRecorder;
    mediaRecorder.start();
    // Start speech recognition
    if (recognitionRef.current) {
      recognitionRef.current.start();
    }
  } catch (error: any) {
    console.error('🚨 Failed to start voice recording:', error);
    if (error.name === 'NotFoundError') {
      setDeviceStatus('not-found');
      setErrorMessage('No microphone found. Please connect a microphone and try again.');
    } else if (error.name === 'NotAllowedError') {
      setPermissionStatus('denied');
      setErrorMessage('Microphone access denied. Please grant permission and try again.');
    } else if (error.name === 'NotReadableError') {
      setErrorMessage('Microphone is being used by another application. Please close other apps and try again.');
    } else if (error.name === 'OverconstrainedError') {
      setErrorMessage('Microphone constraints not supported. Trying with basic settings...');
      // Retry with basic constraints
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach(track => track.stop());
        setTimeout(() => startListening(), 1000);
      } catch (retryError) {
        setErrorMessage('Unable to access microphone with any settings.');
      }
    } else {
      setErrorMessage(`Microphone error: ${error.message || 'Unknown error'}`);
    }
  }
}, [checkMicrophoneDevices, checkMicrophonePermission, permissionStatus]);

  // Request microphone permission explicitly
  const requestMicrophonePermission = async () => {
    try {
      setPermissionStatus('requesting');
      // Try to get user media to trigger permission request
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // If successful, stop the stream immediately
      stream.getTracks().forEach(track => track.stop());
      setPermissionStatus('granted');
      return true;
    } catch (error: any) {
      console.error('Microphone permission denied:', error);
      setPermissionStatus('denied');
      return false;
    }
  };

  // Stop listening and send transcript
  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsListening(false);
    // Clear silence timer
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    // Always send the audioBlob to backend, even if transcript is empty
    setTimeout(() => {
      if (!transcript.trim()) {
        setErrorMessage('No transcript detected, sending audio to backend for processing...');
      }
      console.log('🗣️ Sending voice input:', transcript);
      onVoiceInput(transcript.trim(), audioBlob);
      setTranscript('');
      setAudioBlob(null);
    }, 500);
  }, [transcript, audioBlob, onVoiceInput]);

  useEffect(() => {
    // Check for browser support and permissions
    const initializeVoiceAssistant = async () => {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const isRecognitionSupported = !!SpeechRecognition;
      const isMediaRecorderSupported = !!window.MediaRecorder;
      setIsSupported(isRecognitionSupported && isMediaRecorderSupported);
      if (isRecognitionSupported) {
        const recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'en-US';

        recognition.onstart = () => {
          console.log('🎤 Voice recognition started');
          setIsListening(true);
        };

        recognition.onresult = (event: any) => {
          let finalTranscript = '';
          let interimTranscript = '';
          for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (result.isFinal) {
              finalTranscript += result[0].transcript;
              setConfidence(result[0].confidence);
            } else {
              interimTranscript += result[0].transcript;
            }
          }
          const fullTranscript = finalTranscript + interimTranscript;
          setTranscript(fullTranscript);

          // Reset silence timer on every result
          if (silenceTimerRef.current) {
            clearTimeout(silenceTimerRef.current);
          }
          // If user is speaking, wait for 5 seconds of silence before auto-stopping
          silenceTimerRef.current = setTimeout(() => {
            if (recognitionRef.current && isListening) {
              stopListening();
            }
          }, 5000);
        };

        recognition.onerror = (event: any) => {
          console.error('🚨 Speech recognition error:', event.error);
          setIsListening(false);
          // Handle common errors gracefully
          if (event.error === 'not-allowed') {
            setPermissionStatus('denied');
          } else if (event.error === 'network') {
            console.warn('Network error in speech recognition, continuing with recorded audio...');
          } else if (event.error === 'no-speech') {
            setErrorMessage('No speech detected. Please try again and speak clearly into your microphone.');
          }
        };

        recognition.onend = () => {
          console.log('🎤 Voice recognition ended');
          setIsListening(false);
        };

        recognitionRef.current = recognition;
      }
    };
    initializeVoiceAssistant();
  }, [isListening, stopListening]);
// ...existing code...

  const handleVoiceToggle = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  if (!isSupported) {
    return (
      <div className="voice-assistant-unsupported">
        <button disabled className="voice-btn voice-btn-disabled" title="Voice features not supported in this browser">
          🚫
        </button>
      </div>
    );
  }

  // Show device not found error
  if (deviceStatus === 'not-found') {
    return (
      <div className="voice-assistant">
        <button 
          className="voice-btn voice-btn-permission"
          onClick={async () => {
            const devicesAvailable = await checkMicrophoneDevices();
            if (devicesAvailable) {
              await checkMicrophonePermission();
            }
          }}
          title="Retry microphone detection"
        >
          🔄
        </button>
        <div className="voice-error">
          {errorMessage || 'No microphone found'}
          <br />
          <small>Click to retry detection</small>
        </div>
      </div>
    );
  }

  // Show permission request button if needed
  if (permissionStatus === 'denied') {
    return (
      <div className="voice-assistant">
        <button
          className="voice-btn voice-btn-permission"
          onClick={requestMicrophonePermission}
          title="Click to request microphone permissions"
        >
          🔒
        </button>
        <div className="voice-permission-text">
          Microphone access required. Click to grant permission.
        </div>
      </div>
    );
  }

  return (
    <div className="voice-assistant">
      <button
        className={`voice-btn ${isListening ? 'voice-btn-active' : ''} ${disabled || isLoading || permissionStatus === 'requesting' ? 'voice-btn-disabled' : ''}`}
        onClick={handleVoiceToggle}
        disabled={disabled || isLoading || permissionStatus === 'requesting'}
        title={
          permissionStatus === 'requesting' 
            ? 'Requesting microphone access...' 
            : isListening 
              ? 'Click to stop recording' 
              : 'Click to start voice input'
        }
      >
        {isLoading ? (
          <div className="voice-loading">⏳</div>
        ) : permissionStatus === 'requesting' ? (
          <div className="voice-requesting">🔄</div>
        ) : isListening ? (
          <div className="voice-recording">
            🎤
            <div className="voice-pulse"></div>
          </div>
        ) : (
          '🎙️'
        )}
      </button>
      
      {/* Show error message if any */}
      {errorMessage && (
        <div className="voice-error">
          {errorMessage}
        </div>
      )}
      
      {isListening && (
        <div className="voice-status">
          <div className="voice-transcript">
            {transcript || 'Listening...'}
          </div>
          {confidence > 0 && (
            <div className="voice-confidence">
              Confidence: {Math.round(confidence * 100)}%
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default VoiceAssistant;
