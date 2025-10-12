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
import '@livekit/components-styles';

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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mb-4 mx-auto"></div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Connecting to Interview Room</h2>
          <p className="text-gray-600">Please wait while we set up your video conference...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 text-center max-w-md w-full">
          <div className="text-red-600 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 18.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Connection Error</h2>
          <p className="text-gray-600 mb-6">{error}</p>
          <button
            onClick={onLeave}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            Go Back to Home
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header with room info and controls */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-gray-900">
                Interview: {roomName}
              </h1>
              <div className="ml-4 text-sm text-gray-600">
                Participant: {participantName}
              </div>
            </div>
            <button
              onClick={onLeave}
              className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 transition-colors"
            >
              Leave Room
            </button>
          </div>
        </div>
      </div>

      {/* Video Conference Container */}
      <div className="flex-1 p-4">
        <div className="max-w-7xl mx-auto">
          <div className="bg-white rounded-lg shadow-xl overflow-hidden" style={{ height: 'calc(100vh - 120px)' }}>
            <LiveKitRoom
              video={true}
              audio={true}
              token={token}
              serverUrl={wsUrl}
              data-lk-theme="default"
              style={{ height: '100%' }}
              onDisconnected={onLeave}
              className="lk-room-container"
            >
              {/* Custom styled video conference */}
              <div className="h-full relative">
                <VideoConference />
                <RoomAudioRenderer />
              </div>
            </LiveKitRoom>
          </div>
        </div>
      </div>
    </div>
  );
}