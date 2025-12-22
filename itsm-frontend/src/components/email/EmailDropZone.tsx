/**
 * EmailDropZone Component
 * Drag-and-drop zone for uploading .eml or .msg email files
 */
import { useState, useCallback } from 'react';
import { Upload, FileText, AlertCircle, Loader2 } from 'lucide-react';

interface EmailDropZoneProps {
    onFileUpload: (file: File) => Promise<void>;
    isLoading?: boolean;
    error?: string | null;
}

const ACCEPTED_TYPES = ['.eml', '.msg'];

export function EmailDropZone({ onFileUpload, isLoading = false, error }: EmailDropZoneProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const [fileName, setFileName] = useState<string | null>(null);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
    }, []);

    const validateFile = useCallback((file: File): boolean => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        return ACCEPTED_TYPES.includes(ext);
    }, []);

    const handleFile = useCallback(async (file: File) => {
        if (!validateFile(file)) {
            return;
        }
        setFileName(file.name);
        await onFileUpload(file);
        setFileName(null);
    }, [validateFile, onFileUpload]);

    const handleDrop = useCallback(async (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0) {
            await handleFile(files[0]);
        }
    }, [handleFile]);

    const handleFileInput = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (files && files.length > 0) {
            await handleFile(files[0]);
        }
        e.target.value = ''; // Reset input
    }, [handleFile]);

    return (
        <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
                relative border-2 border-dashed rounded-2xl p-8 transition-all duration-200 text-center
                ${isDragOver
                    ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                    : 'border-surface-300 dark:border-surface-700 hover:border-surface-400 dark:hover:border-surface-600'}
                ${error ? 'border-red-500 bg-red-50 dark:bg-red-900/10' : ''}
            `}
        >
            <input
                type="file"
                accept=".eml,.msg"
                onChange={handleFileInput}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                disabled={isLoading}
            />

            <div className="flex flex-col items-center gap-4">
                {isLoading ? (
                    <>
                        <div className="w-16 h-16 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                            <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
                        </div>
                        <div>
                            <p className="font-medium text-surface-900 dark:text-white">
                                Processing email...
                            </p>
                            {fileName && (
                                <p className="text-sm text-surface-500 mt-1">{fileName}</p>
                            )}
                        </div>
                    </>
                ) : error ? (
                    <>
                        <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center">
                            <AlertCircle className="w-8 h-8 text-red-600 dark:text-red-400" />
                        </div>
                        <div>
                            <p className="font-medium text-red-600 dark:text-red-400">
                                Upload failed
                            </p>
                            <p className="text-sm text-surface-500 mt-1">{error}</p>
                        </div>
                    </>
                ) : (
                    <>
                        <div className={`
                            w-16 h-16 rounded-full flex items-center justify-center transition-colors
                            ${isDragOver
                                ? 'bg-primary-500 text-white'
                                : 'bg-surface-100 dark:bg-surface-800 text-surface-500'}
                        `}>
                            {isDragOver ? <FileText className="w-8 h-8" /> : <Upload className="w-8 h-8" />}
                        </div>
                        <div>
                            <p className="font-medium text-surface-900 dark:text-white">
                                {isDragOver ? 'Drop email file here' : 'Drag and drop email file'}
                            </p>
                            <p className="text-sm text-surface-500 mt-1">
                                or click to browse • Supports .eml and .msg files
                            </p>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}
