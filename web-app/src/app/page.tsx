'use client';

import { useState } from 'react';
import InterviewRoom from './components/InterviewRoom';

export default function Home() {
  const [inRoom, setInRoom] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [participantName, setParticipantName] = useState('');
  const [useAI, setUseAI] = useState(false);

  const joinRoom = () => {
    if (roomName.trim() && participantName.trim()) {
      setInRoom(true);
    }
  };

  const leaveRoom = () => {
    setInRoom(false);
    setRoomName('');
    setParticipantName('');
    setUseAI(false);
  };

  if (inRoom) {
    return (
      <InterviewRoom
        roomName={roomName}
        participantName={participantName}
        onLeave={leaveRoom}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            LiveKit Interview
          </h1>
          <p className="text-gray-600">
            Join or create an interview room
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <label htmlFor="roomName" className="block text-sm font-medium text-gray-700 mb-2">
              Room Name
            </label>
            <input
              id="roomName"
              type="text"
              value={roomName}
              onChange={(e) => setRoomName(e.target.value)}
              placeholder="Enter room name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            />
          </div>

          <div>
            <label htmlFor="participantName" className="block text-sm font-medium text-gray-700 mb-2">
              Your Name
            </label>
            <input
              id="participantName"
              type="text"
              value={participantName}
              onChange={(e) => setParticipantName(e.target.value)}
              placeholder="Enter your name..."
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
            />
          </div>

          <div className="flex items-center">
            <input
              id="useAI"
              type="checkbox"
              checked={useAI}
              onChange={(e) => setUseAI(e.target.checked)}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="useAI" className="ml-2 block text-sm text-gray-700">
              Include AI Interviewer
              <span className="text-gray-500 text-xs block">
                An AI assistant will join to conduct the interview
              </span>
            </label>
          </div>

          <button
            onClick={joinRoom}
            disabled={!roomName.trim() || !participantName.trim()}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Join Interview Room
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="text-sm font-medium text-gray-900 mb-2">Features:</h3>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Video and audio communication</li>
            <li>• Real-time connection</li>
            <li>• Multi-participant support</li>
            <li>• Screen sharing capabilities</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
