import { useState } from 'react';
import { createPortal } from 'react-dom';

interface ConfirmDialogProps {
    isOpen: boolean;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    isDangerous?: boolean;
    isLoading?: boolean;
    onConfirm: () => void;
    onCancel: () => void;
}

export function ConfirmDialog({
    isOpen,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    isDangerous = false,
    isLoading = false,
    onConfirm,
    onCancel,
}: ConfirmDialogProps) {
    if (!isOpen) return null;

    const modalContent = (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4 animate-fade-in">
            {/* Backdrop with subtle grain */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm transition-opacity backdrop-grain"
                onClick={onCancel}
            />

            {/* Dialog Panel with enhanced glass effect */}
            <div
                className="relative z-10 w-full max-w-md bg-white dark:bg-surface-900 rounded-2xl shadow-depth-3 border border-white/10 dark:border-white/5 overflow-hidden animate-scale-in"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Animated gradient border on top */}
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary-500/60 to-transparent" />

                {/* Inner highlight */}
                <div className="absolute top-0 left-0 right-0 h-24 bg-gradient-to-b from-white/5 to-transparent pointer-events-none" />

                {/* Header */}
                <div className="p-6 pb-2 relative">
                    <h2 className="text-xl font-semibold text-surface-900 dark:text-white text-emphasis">
                        {title}
                    </h2>
                </div>

                {/* Content */}
                <div className="px-6 py-2">
                    <p className="text-surface-600 dark:text-surface-300 text-sm leading-relaxed">
                        {message}
                    </p>
                </div>

                {/* Footer Actions */}
                <div className="p-6 flex items-center justify-end gap-3 bg-surface-50/50 dark:bg-surface-800/30 border-t border-surface-100 dark:border-surface-800">
                    <button
                        type="button"
                        className="btn btn-ghost"
                        onClick={onCancel}
                        disabled={isLoading}
                    >
                        {cancelText}
                    </button>
                    <button
                        type="button"
                        className={`btn ${isDangerous ? 'btn-danger' : 'btn-accent'}`}
                        onClick={onConfirm}
                        disabled={isLoading}
                    >
                        {isLoading ? 'Processing...' : confirmText}
                    </button>
                </div>
            </div>
        </div>
    );

    return createPortal(modalContent, document.body);
}

export function useConfirmDialog() {
    const [isOpen, setIsOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const open = () => setIsOpen(true);
    const close = () => {
        if (!isLoading) {
            setIsOpen(false);
        }
    };

    return {
        isOpen,
        isLoading,
        setIsLoading,
        open,
        close,
    };
}
