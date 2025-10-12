import { AccessToken } from 'livekit-server-sdk';
import { NextRequest, NextResponse } from 'next/server';

// Environment variables - these should be set in production
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;

// Validate that all required environment variables are set
if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET || !LIVEKIT_URL) {
    throw new Error('Missing required LiveKit environment variables. Please check your .env.local file.');
}

export async function POST(request: NextRequest) {
    try {
        const body = await request.json();
        const { roomName, participantName, participantIdentity, uploadResult } = body;

        if (!roomName || !participantName) {
            return NextResponse.json(
                { error: 'Missing required fields: roomName, participantName' },
                { status: 400 }
            );
        }

        // Create access token
        const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
            identity: participantIdentity || participantName,
            name: participantName,
        });

        // Grant permissions for the interview room
        token.addGrant({
            room: roomName,
            roomJoin: true,
            canPublish: true,
            canSubscribe: true,
            canPublishData: true,
        });
        token.metadata = JSON.stringify({ uploadResult })

        const jwt = await token.toJwt();

        return NextResponse.json({
            token: jwt,
            url: LIVEKIT_URL,
            roomName,
            participantName,
        });
    } catch (error) {
        console.error('Error generating token:', error);
        return NextResponse.json(
            { error: 'Failed to generate token' },
            { status: 500 }
        );
    }
}

export async function GET() {
    return NextResponse.json({
        message: 'Interview API endpoint - use POST to generate tokens',
        requiredFields: ['roomName', 'participantName'],
        optionalFields: ['participantIdentity'],
    });
}