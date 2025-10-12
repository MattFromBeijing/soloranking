'use client';

import { useState, useCallback } from 'react';

interface UploadFormProps {
  onJoinRoom: (roomName: string, participantName: string, useAI: boolean, uploadResult: any) => void;
}

export default function UploadForm({ onJoinRoom }: UploadFormProps) {
  const [roomName, setRoomName] = useState('');
  const [participantName, setParticipantName] = useState('');
  const [useAI, setUseAI] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingComplete, setProcessingComplete] = useState(false);
  const [uploadError, setUploadError] = useState<string>('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploadResult, setUploadResult] = useState<any>(null);

  const uploadPDF = async (file: File) => {
    setIsUploading(true);
    setUploadError('');
    setUploadSuccess(false);
    setIsProcessing(false);
    setProcessingComplete(false);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://127.0.0.1:5000/upload-pdf-llm', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }
      
      // Upload successful, now start processing
      setIsUploading(false);
      setUploadSuccess(true);
      setIsProcessing(true);
      
      const result = await response.json();
      setUploadResult(result);
      
      // Simulate processing time or wait for actual processing completion
      // You can modify this based on your backend response
      setTimeout(() => {
        setIsProcessing(false);
        setProcessingComplete(true);
        console.log('Upload and processing successful:', result);
      }, 2000); // 2 second delay to show processing state
      
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : 'Upload failed');
      setUploadSuccess(false);
      setIsUploading(false);
      setIsProcessing(false);
      setProcessingComplete(false);
    }
  };

  const handleFileSelect = useCallback((file: File) => {
    if (file.type !== 'application/pdf') {
      setUploadError('Please select a PDF file');
      return;
    }
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      setUploadError('File size must be less than 10MB');
      return;
    }
    
    setUploadedFile(file);
    setUploadError('');
    uploadPDF(file);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  }, [handleFileSelect]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleJoinRoom = () => {
    if (roomName.trim() && participantName.trim() && processingComplete) {
      onJoinRoom(roomName, participantName, useAI, uploadResult);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Solo Leveling
          </h1>
          <p className="text-gray-600">
            Level up your skills with AI-powered case interviews!
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

          {/* PDF Upload Dropbox */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload Casebook (PDF)
            </label>
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`relative border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                isDragOver
                  ? 'border-blue-500 bg-blue-50'
                  : processingComplete
                  ? 'border-green-500 bg-green-50'
                  : isProcessing
                  ? 'border-yellow-500 bg-yellow-50'
                  : uploadSuccess
                  ? 'border-blue-500 bg-blue-50'
                  : uploadError
                  ? 'border-red-500 bg-red-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileInput}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={isUploading || isProcessing}
              />
              
              {isUploading ? (
                <div className="flex flex-col items-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-2"></div>
                  <p className="text-sm text-gray-600">Uploading...</p>
                </div>
              ) : isProcessing ? (
                <div className="flex flex-col items-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600 mb-2"></div>
                  <p className="text-sm text-yellow-700 font-medium">
                    {uploadedFile?.name} uploaded successfully!
                  </p>
                  <p className="text-sm text-gray-600 mt-1">Processing PDF...</p>
                </div>
              ) : processingComplete ? (
                <div className="flex flex-col items-center">
                  <svg className="h-8 w-8 text-green-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm text-green-600 font-medium">
                    {uploadedFile?.name} processed successfully!
                  </p>
                  <p className="text-xs text-green-600 mt-1">Ready to join interview</p>
                </div>
              ) : uploadSuccess ? (
                <div className="flex flex-col items-center">
                  <svg className="h-8 w-8 text-blue-600 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm text-blue-600 font-medium">
                    {uploadedFile?.name} uploaded successfully!
                  </p>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <svg className="h-8 w-8 text-gray-400 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Click to upload</span> or drag and drop
                  </p>
                  <p className="text-xs text-gray-500 mt-1">PDF files only, max 10MB</p>
                </div>
              )}
              
              {uploadError && (
                <div className="mt-2">
                  <p className="text-sm text-red-600">{uploadError}</p>
                </div>
              )}
            </div>
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
            onClick={handleJoinRoom}
            disabled={!roomName.trim() || !participantName.trim() || !processingComplete || isUploading || isProcessing}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {isUploading ? 'Uploading...' :
             isProcessing ? 'Processing PDF...' :
             !processingComplete ? 'Upload PDF to Continue' : 
             'Join Interview Room'}
          </button>
          
          {!processingComplete && !isUploading && !isProcessing && (
            <p className="text-xs text-gray-500 text-center mt-2">
              Please upload your casebook before joining the interview
            </p>
          )}
          
          {isProcessing && (
            <p className="text-xs text-yellow-600 text-center mt-2">
              Processing your PDF... This may take a few moments
            </p>
          )}
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