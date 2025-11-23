'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

interface ResultData {
    hierarchy: any;
    prompts: any[];
}

export default function Results() {
    const [data, setData] = useState<ResultData | null>(null);

    useEffect(() => {
        const stored = localStorage.getItem('ragResult');
        if (stored) {
            try {
                // The result might be a JSON string inside a JSON string if not parsed correctly in backend
                // But our backend returns a dict which is JSONified.
                // However, the LLM returns a string, so we might need to parse it twice if the backend didn't parse it.
                // Let's assume backend returns the raw LLM string for now, or we parse it there.
                // In endpoints.py: jobs[job_id]["result"] = result_json (which is a string from LLM)
                const parsed = JSON.parse(stored);
                // If the LLM returned a stringified JSON, we need to parse again
                const finalData = typeof parsed === 'string' ? JSON.parse(parsed) : parsed;
                setData(finalData);
            } catch (e) {
                console.error("Failed to parse results", e);
            }
        }
    }, []);

    if (!data) return <div className="text-white p-8">Loading results...</div>;

    return (
        <main className="min-h-screen bg-slate-900 text-white p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                        Generated Results
                    </h1>
                    <Link
                        href="/"
                        className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                    >
                        New Search
                    </Link>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Hierarchy View */}
                    <div className="lg:col-span-1 space-y-4">
                        <h2 className="text-xl font-semibold text-slate-300">Topic Hierarchy</h2>
                        <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-4 overflow-auto max-h-[80vh]">
                            <pre className="text-xs text-slate-300 whitespace-pre-wrap">
                                {JSON.stringify(data.hierarchy, null, 2)}
                            </pre>
                        </div>
                    </div>

                    {/* Prompts Grid */}
                    <div className="lg:col-span-2 space-y-4">
                        <h2 className="text-xl font-semibold text-slate-300">Generated Prompts</h2>
                        <div className="grid gap-4">
                            {data.prompts && data.prompts.map((prompt: any, i: number) => (
                                <div
                                    key={i}
                                    className="bg-slate-800/50 border border-slate-700 rounded-xl p-6 hover:border-blue-500/50 transition-colors group"
                                >
                                    <div className="flex justify-between items-start mb-4">
                                        <span className="bg-blue-500/10 text-blue-400 text-xs px-2 py-1 rounded-full">
                                            {prompt.type || 'Prompt'}
                                        </span>
                                        <button
                                            onClick={() => navigator.clipboard.writeText(prompt.content || prompt.text)}
                                            className="text-slate-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            Copy
                                        </button>
                                    </div>
                                    <p className="text-slate-200 leading-relaxed">
                                        {prompt.content || prompt.text || JSON.stringify(prompt)}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </main>
    );
}
