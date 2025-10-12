'use client';

import { useState } from 'react';
import InterviewRoom from './components/InterviewRoom';
import UploadForm from './components/UploadForm';

export default function Home() {
  const [inRoom, setInRoom] = useState(false);
  const [roomName, setRoomName] = useState('');
  const [participantName, setParticipantName] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const handleJoinRoom = (roomName: string, participantName: string, useAI: boolean, uploadResult: any) => {
    setRoomName(roomName);
    setParticipantName(participantName);
    setUseAI(useAI);
    setUploadResult(uploadResult);
    setInRoom(true);
  };

  const handleLeaveRoom = () => {
    setInRoom(false);
    setRoomName('');
    setParticipantName('');
    setUseAI(false);
    setUploadResult(null);
  };

  if (inRoom) {
    return (
      <InterviewRoom
        roomName={roomName}
        participantName={participantName}
        uploadResult={uploadResult}
        onLeave={handleLeaveRoom}
      />
    );
  }

  return <UploadForm onJoinRoom={handleJoinRoom} />;
}
