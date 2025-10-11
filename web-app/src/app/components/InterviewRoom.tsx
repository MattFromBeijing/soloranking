'use client';

import { useEffect, useState } from 'react';
import {
  LiveKitRoom,
  VideoConference,
  GridLayout,
  ParticipantTile,
  RoomAudioRenderer,
  ControlBar,
  useTracks,
} from '@livekit/components-react';
import { Track } from 'livekit-client';

interface InterviewRoomProps {
  roomName: string;
  participantName: string;
  onLeave?: () => void;
}

export default function InterviewRoom({ roomName, participantName, onLeave }: InterviewRoomProps) {
  const [token, setToken] = useState<string>('');
  const [wsUrl, setWsUrl] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const generateToken = async () => {
      try {
        const response = await fetch('/api/interview', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            roomName,
            participantName,
            participantIdentity: participantName.toLowerCase().replace(/\s+/g, '-'),
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to generate token');
        }

        const data = await response.json();
        setToken(data.token);
        setWsUrl(data.url);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    generateToken();
  }, [roomName, participantName]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-lg">Connecting to interview room...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center text-red-600">
          <h2 className="text-xl font-bold mb-2">Connection Error</h2>
          <p className="mb-4">{error}</p>
          <button
            onClick={onLeave}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full">
      <LiveKitRoom
        video={true}
        audio={true}
        token={token}
        serverUrl={wsUrl}
        data-lk-theme="default"
        style={{ height: '100vh' }}
        onDisconnected={onLeave}
      >
        {/* Interview Room Header */}
        <div className="absolute top-4 left-4 z-10 bg-black bg-opacity-50 text-white px-3 py-2 rounded">
          <h3 className="font-semibold">Interview: {roomName}</h3>
          <p className="text-sm">Participant: {participantName}</p>
        </div>

        {/* Main Video Conference */}
        <VideoConference />
        
        {/* Audio renderer for participants */}
        <RoomAudioRenderer />
      </LiveKitRoom>
    </div>
  );
}