'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { AnalysisResult } from '@/types';
import { exportHierarchyToCSV } from '@/utils/csvExport';

export default function Results() {
    const [data, setData] = useState<AnalysisResult | null>(null);

    useEffect(() => {
        const stored = localStorage.getItem('ragResult');
        if (stored) {
            try {
                const parsed = JSON.parse(stored);
                // Handle double-stringified JSON if present
                const finalData = typeof parsed === 'string' ? JSON.parse(parsed) : parsed;
                setData(finalData);
            } catch (e) {
                console.error("Failed to parse results", e);
            }
        }
    }, []);

    const handleExport = () => {
        if (data?.hierarchy) {
            exportHierarchyToCSV(data.hierarchy);
        }
    };

    if (!data) return <div className="text-white p-8">Loading results...</div>;

    return (
        <main className="min-h-screen bg-slate-900 text-white p-8">
            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-8">
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-400">
                        Generated Results
                    </h1>
                    <div className="flex gap-4">
                        {data.hierarchy && (
                            <button
                                onClick={handleExport}
                                className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                                    <polyline points="7 10 12 15 17 10" />
                                    <line x1="12" y1="15" x2="12" y2="3" />
                                </svg>
                                Export CSV
                            </button>
                        )}
                        <Link
                            href="/"
                            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                        >
                            New Search
                        </Link>
                    </div>
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

                    {/* Prompts & Evaluation Grid */}
                    <div className="lg:col-span-2 space-y-8">
                        {/* Evaluation Section */}
                        {data.evaluation && (
                            <div className="space-y-4">
                                <h2 className="text-xl font-semibold text-slate-300">Expert Evaluation</h2>
                                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-6">
                                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                                        <div className="bg-slate-900/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400">Structure</div>
                                            <div className="text-xl font-bold text-blue-400">{data.evaluation.scores.logicalStructure}/10</div>
                                        </div>
                                        <div className="bg-slate-900/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400">Relevance</div>
                                            <div className="text-xl font-bold text-green-400">{data.evaluation.scores.keywordRelevance}/10</div>
                                        </div>
                                        <div className="bg-slate-900/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400">Realism</div>
                                            <div className="text-xl font-bold text-yellow-400">{data.evaluation.scores.searchVolumeRealism}/10</div>
                                        </div>
                                        <div className="bg-slate-900/50 p-3 rounded-lg text-center">
                                            <div className="text-xs text-slate-400">Business</div>
                                            <div className="text-xl font-bold text-purple-400">{data.evaluation.scores.businessValue}/10</div>
                                        </div>
                                    </div>

                                    <div className="space-y-4">
                                        <div>
                                            <h3 className="text-sm font-semibold text-slate-300 mb-2">Analysis</h3>
                                            <p className="text-sm text-slate-400 leading-relaxed">{data.evaluation.hierarchyAnalysis}</p>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                            <div>
                                                <h3 className="text-sm font-semibold text-green-400 mb-2">Strengths</h3>
                                                <ul className="list-disc list-inside text-sm text-slate-400 space-y-1">
                                                    {data.evaluation.strengths.map((s, i) => <li key={i}>{s}</li>)}
                                                </ul>
                                            </div>
                                            <div>
                                                <h3 className="text-sm font-semibold text-red-400 mb-2">Weaknesses</h3>
                                                <ul className="list-disc list-inside text-sm text-slate-400 space-y-1">
                                                    {data.evaluation.weaknesses.map((w, i) => <li key={i}>{w}</li>)}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Prompts Section */}
                        <div className="space-y-4">
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
            </div>
        </main>
    );
}
