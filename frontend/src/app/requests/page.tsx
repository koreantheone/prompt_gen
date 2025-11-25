'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

interface TaskStatus {
    status: 'pending' | 'running' | 'success' | 'error';
    progress: number;
}

interface RequestSummary {
    requestId: string;
    createdAt: string;
    config: {
        prompt: string;
        llm_provider: string;
    };
    tasks: {
        dataCollection: TaskStatus;
        hierarchyGeneration: TaskStatus;
        promptGeneration: TaskStatus;
    };
}

interface RequestListResponse {
    requests: RequestSummary[];
    total: number;
    limit: number;
    offset: number;
}

const StatusIcon = ({ status }: { status: string }) => {
    switch (status) {
        case 'success':
            return <span className="text-green-500 text-xl">✓</span>;
        case 'running':
            return <span className="text-blue-500 text-xl">⏳</span>;
        case 'error':
            return <span className="text-red-500 text-xl">✗</span>;
        default:
            return <span className="text-gray-400 text-xl">○</span>;
    }
};

export default function RequestsPage() {
    const [requests, setRequests] = useState<RequestSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [total, setTotal] = useState(0);

    useEffect(() => {
        fetchRequests();
        // Auto-refresh every 5 seconds
        const interval = setInterval(fetchRequests, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchRequests = async () => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            const response = await fetch(`${apiUrl}/api/requests`);
            const data: RequestListResponse = await response.json();
            setRequests(data.requests);
            setTotal(data.total);
        } catch (error) {
            console.error('Error fetching requests:', error);
        } finally {
            setLoading(false);
        }
    };

    const deleteRequest = async (requestId: string) => {
        if (!confirm('Are you sure you want to delete this request?')) return;

        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
            await fetch(`${apiUrl}/api/requests/${requestId}`, {
                method: 'DELETE',
            });
            fetchRequests();
        } catch (error) {
            console.error('Error deleting request:', error);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diff = now.getTime() - date.getTime();
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor(diff / (1000 * 60));

        if (hours > 24) {
            return date.toLocaleDateString();
        } else if (hours > 0) {
            return `${hours}h ago`;
        } else if (minutes > 0) {
            return `${minutes}m ago`;
        } else {
            return 'Just now';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="max-w-7xl mx-auto">
                    <div className="text-center py-12">
                        <div className="text-xl text-gray-600">Loading requests...</div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto">
                <div className="mb-8 flex justify-between items-center">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900">Request History</h1>
                        <p className="text-gray-600 mt-2">Total: {total} requests</p>
                    </div>
                    <Link
                        href="/"
                        className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
                    >
                        New Request
                    </Link>
                </div>

                {requests.length === 0 ? (
                    <div className="bg-white rounded-lg shadow p-12 text-center">
                        <p className="text-gray-600 text-lg">No requests yet</p>
                        <Link
                            href="/"
                            className="inline-block mt-4 text-blue-600 hover:underline"
                        >
                            Create your first request
                        </Link>
                    </div>
                ) : (
                    <div className="bg-white rounded-lg shadow overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Request ID
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Prompt
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Created
                                    </th>
                                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Data Collection
                                    </th>
                                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Hierarchy
                                    </th>
                                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Prompts
                                    </th>
                                    <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {requests.map((request) => (
                                    <tr key={request.requestId} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <Link
                                                href={`/requests/${request.requestId}`}
                                                className="text-blue-600 hover:underline font-mono text-sm"
                                            >
                                                {request.requestId}
                                            </Link>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-900 max-w-xs truncate">
                                                {request.config.prompt}
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {request.config.llm_provider}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {formatDate(request.createdAt)}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <StatusIcon status={request.tasks.dataCollection.status} />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <StatusIcon status={request.tasks.hierarchyGeneration.status} />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <StatusIcon status={request.tasks.promptGeneration.status} />
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-center">
                                            <div className="flex gap-2 justify-center">
                                                <Link
                                                    href={`/requests/${request.requestId}`}
                                                    className="text-blue-600 hover:text-blue-800 text-sm"
                                                >
                                                    View
                                                </Link>
                                                <button
                                                    onClick={() => deleteRequest(request.requestId)}
                                                    className="text-red-600 hover:text-red-800 text-sm"
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
