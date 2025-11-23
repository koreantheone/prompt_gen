'use client';

import { useEffect, useState, Suspense, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

function DashboardContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const jobId = searchParams.get('jobId');
    const logsEndRef = useRef<HTMLDivElement>(null);

    const [progress, setProgress] = useState(0);
    const [status, setStatus] = useState('Initializing...');
    const [logs, setLogs] = useState<string[]>([]);

    // Auto-scroll to bottom of logs
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [logs]);

    useEffect(() => {
        if (!jobId) return;

        const interval = setInterval(async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const res = await fetch(`${apiUrl}/api/status/${jobId}`);
                if (!res.ok) return;

                const data = await res.json();
                setProgress(data.progress);
                setStatus(data.status);
                setLogs(data.logs || []);

                if (data.status === 'Complete') {
                    clearInterval(interval);
                    // Pass the result to the results page via localStorage or state management
                    localStorage.setItem('ragResult', JSON.stringify(data.result));
                    setTimeout(() => router.push('/results'), 1000);
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [jobId, router]);

    return (
        <main className="min-h-screen bg-slate-900 text-white p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                <h1 className="text-3xl font-bold">Processing Request</h1>

                {/* Progress Bar */}
                <div className="bg-slate-800 rounded-full h-4 overflow-hidden">
                    <div
                        className="bg-blue-500 h-full transition-all duration-500 ease-out"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                {/* Status Card */}
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-semibold text-blue-400">{status}</h2>
                        <span className="text-slate-400">{progress}%</span>
                    </div>

                    {/* Logs Terminal */}
                    <div className="bg-black/50 rounded-lg p-4 h-64 overflow-y-auto font-mono text-sm text-green-400 border border-slate-700/50">
                        {logs.map((log, i) => (
                            <div key={i} className="mb-1">
                                {log}
                            </div>
                        ))}
                        <div ref={logsEndRef} />
                    </div>
                </div>
            </div>
        </main>
    );
}

export default function Dashboard() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <DashboardContent />
        </Suspense>
    );
}
