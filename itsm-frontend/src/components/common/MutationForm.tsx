import { useState } from 'react';
import { createPortal } from 'react-dom';
import { getErrorCode, getErrorMessage } from '../../types/api';
import { AlertCircle } from 'lucide-react';

interface MutationFormProps {
    isOpen: boolean;
    title: string;
    isSubmitting: boolean;
    error: unknown;
    submitText?: string;
    cancelText?: string;
    isDangerous?: boolean;
    isValid: boolean;
    onCancel: () => void;
    onSubmit: () => void;
    children: React.ReactNode;
}

export function MutationForm({
    isOpen,
    title,
    isSubmitting,
    error,
    submitText = 'Submit',
    cancelText = 'Cancel',
    isDangerous = false,
    isValid,
    onCancel,
    onSubmit,
    children,
}: MutationFormProps) {
    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (isValid && !isSubmitting) {
            onSubmit();
        }
    };

    const modalContent = (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 animate-fade-in">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
                onClick={onCancel}
            />

            {/* Dialog Panel */}
            <div
                className="relative z-10 w-full max-w-lg bg-white dark:bg-surface-900 rounded-2xl shadow-modal border border-white/10 overflow-hidden animate-scale-in flex flex-col max-h-[90vh]"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-6 border-b border-surface-100 dark:border-surface-800">
                    <h2 className="text-xl font-semibold text-surface-900 dark:text-white">
                        {title}
                    </h2>
                </div>

                <form onSubmit={handleSubmit} className="flex flex-col flex-1 overflow-hidden">
                    <div className="p-6 overflow-y-auto flex-1 custom-scrollbar">
                        {/* Error display */}
                        {error != null && (
                            <div className="mb-6 p-4 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 flex gap-3 items-start">
                                <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                                <div className="text-sm text-red-700 dark:text-red-400">
                                    <strong className="block mb-1">Error ({getErrorCode(error)})</strong>
                                    {getErrorMessage(error)}
                                </div>
                            </div>
                        )}

                        <div className="space-y-4">
                            {children}
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="p-6 border-t border-surface-100 dark:border-surface-800 bg-surface-50/50 dark:bg-surface-900/50 flex items-center justify-end gap-3 shrink-0">
                        <button
                            type="button"
                            className="btn btn-secondary"
                            onClick={onCancel}
                            disabled={isSubmitting}
                        >
                            {cancelText}
                        </button>
                        <button
                            type="submit"
                            className={`btn ${isDangerous ? 'btn-danger' : 'btn-accent'}`}
                            disabled={!isValid || isSubmitting}
                        >
                            {isSubmitting ? 'Processing...' : submitText}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );

    return createPortal(modalContent, document.body);
}

interface NoteInputProps {
    value: string;
    onChange: (value: string) => void;
    label?: string;
    placeholder?: string;
    required?: boolean;
    disabled?: boolean;
    minLength?: number;
}

export function NoteInput({
    value,
    onChange,
    label = 'Note',
    placeholder = 'Enter a note (required)',
    required = true,
    disabled = false,
    minLength = 1,
}: NoteInputProps) {
    const isValid = !required || value.trim().length >= minLength;

    return (
        <div className="space-y-1.5">
            <label className="text-sm font-medium text-surface-700 dark:text-surface-300">
                {label}
                {required && <span className="text-red-500 ml-1">*</span>}
            </label>
            <textarea
                className={`input min-h-[100px] resize-none ${!isValid && value ? 'input-error' : ''}`}
                value={value}
                onChange={(e) => onChange(e.target.value)}
                placeholder={placeholder}
                required={required}
                disabled={disabled}
            />
            {!isValid && value && (
                <p className="text-xs text-red-500">Note is required</p>
            )}
        </div>
    );
}

export function useMutationForm() {
    const [isOpen, setIsOpen] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<unknown>(null);

    const open = () => {
        setError(null);
        setIsOpen(true);
    };

    const close = () => {
        if (!isSubmitting) {
            setIsOpen(false);
            setError(null);
        }
    };

    const reset = () => {
        setError(null);
        setIsSubmitting(false);
    };

    return {
        isOpen,
        isSubmitting,
        error,
        setIsSubmitting,
        setError,
        open,
        close,
        reset,
    };
}
