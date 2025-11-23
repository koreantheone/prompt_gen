export type Mode = 'Light' | 'Standard' | 'Full';

export interface SearchParams {
    prompt: string;
    keywords: string;
    country: string;
    language: string;
    mode: Mode;
    apis: string[];
    llm_provider: string;
}

export const COUNTRIES = [
    { code: 'us', name: 'United States' },
    { code: 'kr', name: 'South Korea' },
    { code: 'jp', name: 'Japan' },
    { code: 'uk', name: 'United Kingdom' },
];

export const LANGUAGES = [
    { code: 'en', name: 'English' },
    { code: 'ko', name: 'Korean' },
    { code: 'ja', name: 'Japanese' },
];

export const API_OPTIONS = [
    {
        category: 'Keywords Data',
        items: [
            { id: 'google_ads', label: 'Google Ads' },
            { id: 'bing_ads', label: 'Bing Ads' },
            { id: 'google_trends', label: 'Google Trends' },
        ]
    },
    {
        category: 'SERP',
        items: [
            { id: 'google_search', label: 'Google Search' },
            { id: 'bing_search', label: 'Bing Search' },
            { id: 'naver_search', label: 'Naver (Korea Only)' },
        ]
    },
    {
        category: 'Social Media',
        items: [
            { id: 'facebook', label: 'Facebook' },
            { id: 'reddit', label: 'Reddit' },
        ]
    },
    {
        category: 'Reviews',
        items: [
            { id: 'google_reviews', label: 'Google Reviews' },
            { id: 'amazon_reviews', label: 'Amazon Reviews' },
        ]
    }
];

export interface HierarchyNode {
    name: string;
    value: number;
    description?: string;
    children?: HierarchyNode[];
}

export interface EvaluationScore {
    logicalStructure: number;
    keywordRelevance: number;
    searchVolumeRealism: number;
    businessValue: number;
}

export interface Evaluation {
    scores: EvaluationScore;
    totalScore: number;
    reasoning: string;
    strengths: string[];
    weaknesses: string[];
    hierarchyAnalysis: string;
}

export interface AnalysisResult {
    hierarchy: HierarchyNode;
    prompts: any[];
    evaluation?: Evaluation;
}
