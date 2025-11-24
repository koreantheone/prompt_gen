'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';

interface TaskData {
    status: 'pending' | 'running' | 'success' | 'error';
    startedAt: string | null;
    completedAt: string | null;
    error: string | null;
    progress: number;
    logs: string[];
    data: any;
}

interface Request {
    requestId: string;
    createdAt: string;
    updatedAt: string;
    config: {
        prompt: string;
        keywords: string;
        country: string;
        language: string;
        mode: string;
        apis: string[];
        llm_provider: string;
        include_evaluation: boolean;
    };
    tasks: {
        dataCollection: TaskData;
        hierarchyGeneration: TaskData;
        promptGeneration: TaskData;
    };
}

const StatusBadge = ({ status }: { status: string }) => {
    const colors = {
        pending: 'bg-gray-200 text-gray-700',
        running: 'bg-blue-200 text-blue-700',
        success: 'bg-green-200 text-green-700',
        error: 'bg-red-200 text-red-700',
    };

    return (
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${colors[status as keyof typeof colors]}`}>
            {status.toUpperCase()}
        </span>
    );
};

export default function RequestDetailPage() {
    const params = useParams();
    const router = useRouter();
    const requestId = params.id as string;

    const [request, setRequest] = useState<Request | null>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'overview' | 'data' | 'hierarchy' | 'prompts'>('overview');

    useEffect(() => {
        if (requestId) {
            fetchRequest();
            // Auto-refresh every 3 seconds
            const interval = setInterval(fetchRequest, 3000);
            return () => clearInterval(interval);
        }
    }, [requestId]);

    const fetchRequest = async () => {
        try {
            const response = await fetch(`http://localhost:8000/api/requests/${requestId}`);
            if (!response.ok) throw new Error('Request not found');
            const data = await response.json();
            setRequest(data);
        } catch (error) {
            console.error('Error fetching request:', error);
        } finally {
            setLoading(false);
        }
    };

    const retryTask = async (taskName: string) => {
        try {
            await fetch(`http://localhost:8000/api/requests/${requestId}/tasks/${taskName}/execute`, {
                method: 'POST',
            });
            fetchRequest();
        } catch (error) {
            console.error('Error retrying task:', error);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="text-center py-12">
                    <div className="text-xl text-gray-600">Loading request...</div>
                </div>
            </div>
        );
    }

    if (!request) {
        return (
            <div className="min-h-screen bg-gray-50 p-8">
                <div className="text-center py-12">
                    <div className="text-xl text-gray-600">Request not found</div>
                    <Link href="/requests" className="text-blue-600 hover:underline mt-4 inline-block">
                        Back to requests
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-7xl mx-auto">
                {/* Header */}
                <div className="mb-6">
                    <Link href="/requests" className="text-blue-600 hover:underline mb-4 inline-block">
                        ← Back to requests
                    </Link>
                    <h1 className="text-3xl font-bold text-gray-900 font-mono">{request.requestId}</h1>
                    <p className="text-gray-600 mt-2">Created: {new Date(request.createdAt).toLocaleString()}</p>
                </div>

                {/* Tabs */}
                <div className="bg-white rounded-lg shadow mb-6">
                    <div className="border-b border-gray-200">
                        <nav className="flex -mb-px">
                            {[
                                { id: 'overview', label: 'Overview' },
                                { id: 'data', label: 'Data Collection' },
                                { id: 'hierarchy', label: 'Hierarchy' },
                                { id: 'prompts', label: 'Prompts' },
                            ].map((tab) => (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={`px-6 py-4 text-sm font-medium border-b-2 ${activeTab === tab.id
                                            ? 'border-blue-500 text-blue-600'
                                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                                        }`}
                                >
                                    {tab.label}
                                </button>
                            ))}
                        </nav>
                    </div>

                    <div className="p-6">
                        {/* Overview Tab */}
                        {activeTab === 'overview' && (
                            <div className="space-y-6">
                                <div>
                                    <h3 className="text-lg font-semibold mb-4">Configuration</h3>
                                    <div className="grid grid-cols-2 gap-4 bg-gray-50 p-4 rounded">
                                        <div>
                                            <span className="text-sm text-gray-600">Prompt:</span>
                                            <p className="font-medium">{request.config.prompt}</p>
                                        </div>
                                        <div>
                                            <span className="text-sm text-gray-600">LLM Provider:</span>
                                            <p className="font-medium">{request.config.llm_provider}</p>
                                        </div>
                                        <div>
                                            <span className="text-sm text-gray-600">Country:</span>
                                            <p className="font-medium">{request.config.country}</p>
                                        </div>
                                        <div>
                                            <span className="text-sm text-gray-600">Language:</span>
                                            <p className="font-medium">{request.config.language}</p>
                                        </div>
                                        <div>
                                            <span className="text-sm text-gray-600">APIs:</span>
                                            <p className="font-medium">{request.config.apis.join(', ')}</p>
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-lg font-semibold mb-4">Task Status</h3>
                                    <div className="space-y-4">
                                        {Object.entries(request.tasks).map(([taskName, task]) => (
                                            <div key={taskName} className="border rounded-lg p-4">
                                                <div className="flex justify-between items-center mb-2">
                                                    <h4 className="font-medium capitalize">{taskName.replace(/([A-Z])/g, ' $1').trim()}</h4>
                                                    <StatusBadge status={task.status} />
                                                </div>
                                                <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                                                    <div
                                                        className="bg-blue-600 h-2 rounded-full transition-all"
                                                        style={{ width: `${task.progress}%` }}
                                                    />
                                                </div>
                                                <div className="text-sm text-gray-600">
                                                    Progress: {task.progress}%
                                                </div>
                                                {task.error && (
                                                    <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                                                        {task.error}
                                                    </div>
                                                )}
                                                <button
                                                    onClick={() => retryTask(taskName)}
                                                    className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                                                >
                                                    Re-run Task
                                                </button>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Data Collection Tab */}
                        {activeTab === 'data' && (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-lg font-semibold">Data Collection</h3>
                                    <button
                                        onClick={() => retryTask('dataCollection')}
                                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                    >
                                        Re-run Task
                                    </button>
                                </div>

                                <div>
                                    <h4 className="font-medium mb-2">Generated Keywords ({request.tasks.dataCollection.data.generatedKeywords?.length || 0})</h4>
                                    <div className="bg-gray-50 p-4 rounded max-h-60 overflow-y-auto">
                                        <div className="flex flex-wrap gap-2">
                                            {request.tasks.dataCollection.data.generatedKeywords?.map((kw: string, i: number) => (
                                                <span key={i} className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm">
                                                    {kw}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium mb-2">API Responses ({request.tasks.dataCollection.data.apiResponses?.length || 0})</h4>
                                    <div className="bg-gray-50 p-4 rounded max-h-96 overflow-y-auto">
                                        <pre className="text-xs">{JSON.stringify(request.tasks.dataCollection.data.apiResponses, null, 2)}</pre>
                                    </div>
                                </div>

                                <div>
                                    <h4 className="font-medium mb-2">Logs</h4>
                                    <div className="bg-gray-900 text-green-400 p-4 rounded max-h-60 overflow-y-auto font-mono text-xs">
                                        {request.tasks.dataCollection.logs.map((log, i) => (
                                            <div key={i}>{log}</div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Hierarchy Tab */}
                        {activeTab === 'hierarchy' && (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-lg font-semibold">Hierarchy Generation</h3>
                                    <button
                                        onClick={() => retryTask('hierarchyGeneration')}
                                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                    >
                                        Re-run Task
                                    </button>
                                </div>

                                {request.tasks.hierarchyGeneration.data.hierarchy && (
                                    <div>
                                        <h4 className="font-medium mb-2">Generated Hierarchy</h4>
                                        <div className="bg-gray-50 p-4 rounded max-h-96 overflow-y-auto">
                                            <pre className="text-xs">{JSON.stringify(request.tasks.hierarchyGeneration.data.hierarchy, null, 2)}</pre>
                                        </div>
                                    </div>
                                )}

                                {request.tasks.hierarchyGeneration.data.evaluation && (
                                    <div>
                                        <h4 className="font-medium mb-2">Evaluation</h4>
                                        <div className="bg-gray-50 p-4 rounded">
                                            <pre className="text-xs">{JSON.stringify(request.tasks.hierarchyGeneration.data.evaluation, null, 2)}</pre>
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <h4 className="font-medium mb-2">Logs</h4>
                                    <div className="bg-gray-900 text-green-400 p-4 rounded max-h-60 overflow-y-auto font-mono text-xs">
                                        {request.tasks.hierarchyGeneration.logs.map((log, i) => (
                                            <div key={i}>{log}</div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Prompts Tab */}
                        {activeTab === 'prompts' && (
                            <div className="space-y-4">
                                <div className="flex justify-between items-center">
                                    <h3 className="text-lg font-semibold">Prompt Generation</h3>
                                    <button
                                        onClick={() => retryTask('promptGeneration')}
                                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                                    >
                                        Re-run Task
                                    </button>
                                </div>

                                {request.tasks.promptGeneration.data.prompts && (
                                    <div>
                                        <h4 className="font-medium mb-2">Generated Prompts ({request.tasks.promptGeneration.data.prompts.length})</h4>
                                        <div className="space-y-4">
                                            {request.tasks.promptGeneration.data.prompts.map((prompt: any, i: number) => (
                                                <div key={i} className="border rounded-lg p-4 bg-gray-50">
                                                    <div className="font-medium mb-2">{prompt.topic || `Prompt ${i + 1}`}</div>
                                                    <div className="text-sm text-gray-700">{prompt.content || JSON.stringify(prompt)}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                <div>
                                    <h4 className="font-medium mb-2">Logs</h4>
                                    <div className="bg-gray-900 text-green-400 p-4 rounded max-h-60 overflow-y-auto font-mono text-xs">
                                        {request.tasks.promptGeneration.logs.map((log, i) => (
                                            <div key={i}>{log}</div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
