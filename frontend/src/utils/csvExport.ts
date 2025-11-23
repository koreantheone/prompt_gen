import { HierarchyNode } from '@/types';

/**
 * Converts hierarchy data to CSV format string
 * Structure: Depth1, Depth2, Depth3
 */
export const convertToCSV = (data: HierarchyNode): string => {
    const rows: string[] = ["Depth1,Depth2,Depth3"];

    const escapeCSV = (str: string): string => {
        if (str.includes(",") || str.includes('"') || str.includes("\n")) {
            return `"${str.replace(/"/g, '""')}"`;
        }
        return str;
    };

    const traverse = (node: HierarchyNode, depth: number, path: string[]) => {
        // Skip root node if it's just a container (e.g. "Total" or "전체")
        if (depth === 0) {
            if (node.children) {
                node.children.forEach(child => traverse(child, depth + 1, []));
            }
            return;
        }

        const currentPath = [...path, node.name];

        // If it's a leaf node or we are at depth 3
        if (!node.children || node.children.length === 0 || depth === 3) {
            // Pad with empty strings if depth is less than 3
            const row = [...currentPath];
            while (row.length < 3) {
                row.push("");
            }
            rows.push(row.map(escapeCSV).join(","));
        } else {
            // If it has children, traverse them
            // Also add the current node as a row if needed, but usually we want leaf nodes
            // For this specific format (Depth1, Depth2, Depth3), we typically want to show the full path for each leaf
            // If a node has children, we don't add it as a row itself, but recurse
            node.children.forEach(child => traverse(child, depth + 1, currentPath));
        }
    };

    traverse(data, 0, []);
    return rows.join("\n");
};

/**
 * Triggers a download of the CSV content
 */
export const downloadCSV = (csvContent: string, filename: string): void => {
    const BOM = "\uFEFF"; // UTF-8 BOM for Excel compatibility
    const blob = new Blob([BOM + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = "hidden";

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
};

/**
 * Main function to export hierarchy to CSV
 */
export const exportHierarchyToCSV = (data: HierarchyNode): void => {
    try {
        const csvContent = convertToCSV(data);

        const timestamp = new Date().toISOString().replace(/[:.]/g, "-").slice(0, -19) +
            new Date().toISOString().slice(11, 19).replace(/:/g, "-");
        // Simplified timestamp: YYYY-MM-DD-HH-mm-ss
        const date = new Date();
        const formattedDate = date.toISOString().split('T')[0];
        const formattedTime = date.toTimeString().split(' ')[0].replace(/:/g, '-');

        const filename = `industry-analysis-${formattedDate}-${formattedTime}.csv`;

        downloadCSV(csvContent, filename);
    } catch (error) {
        console.error("Failed to export CSV:", error);
        throw error;
    }
};
