/**
 * EmailPreviewModal Component
 * Full-screen modal for previewing email with action buttons
 */
import { useState } from 'react';
import { X, Mail, Paperclip, Trash2, Inbox, Ticket, Loader2 } from 'lucide-react';
import type { EmailIngest } from '../../api/email';
import { discardEmail, processEmail } from '../../api/email';
import { formatDateIST } from '../../utils/dateFormat';

interface EmailPreviewModalProps {
    email: EmailIngest;
    onClose: () => void;
    onActionComplete: () => void;
}

interface CategoryOption {
    id: string;
    name: string;
}

interface SubCategoryOption {
    id: string;
    name: string;
}

export function EmailPreviewModal({ email, onClose, onActionComplete }: EmailPreviewModalProps) {
    const [isProcessing, setIsProcessing] = useState(false);
    const [showDiscardPrompt, setShowDiscardPrompt] = useState(false);
    const [showConvertForm, setShowConvertForm] = useState(false);
    const [discardReason, setDiscardReason] = useState('');
    const [error, setError] = useState<string | null>(null);

    // Convert form state
    const [categories, setCategories] = useState<CategoryOption[]>([]);
    const [subcategories, setSubcategories] = useState<SubCategoryOption[]>([]);
    const [selectedCategory, setSelectedCategory] = useState('');
    const [selectedSubcategory, setSelectedSubcategory] = useState('');
    const [ticketTitle, setTicketTitle] = useState(email.subject || '');
    const [ticketDescription, setTicketDescription] = useState(email.body_text || '');

    // Load categories when convert form opens
    const handleShowConvertForm = async () => {
        setShowConvertForm(true);
        try {
            const { get } = await import('../../api/client');
            const cats = await get<CategoryOption[]>('/api/categories/');
            setCategories(cats);
        } catch {
            setError('Failed to load categories');
        }
    };

    // Load subcategories when category changes
    const handleCategoryChange = async (categoryId: string) => {
        setSelectedCategory(categoryId);
        setSelectedSubcategory('');
        if (categoryId) {
            try {
                const { get } = await import('../../api/client');
                const subs = await get<SubCategoryOption[]>(`/api/categories/${categoryId}/subcategories/`);
                setSubcategories(subs);
            } catch {
                setError('Failed to load subcategories');
            }
        }
    };

    // Handle discard action
    const handleDiscard = async () => {
        if (!discardReason.trim()) {
            setError('Please provide a reason for discarding');
            return;
        }
        setIsProcessing(true);
        setError(null);
        try {
            await discardEmail(email.id, discardReason);
            onActionComplete();
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to discard email');
        } finally {
            setIsProcessing(false);
        }
    };

    // Handle convert to ticket
    const handleConvertToTicket = async () => {
        if (!selectedCategory || !selectedSubcategory) {
            setError('Please select category and subcategory');
            return;
        }
        if (!ticketTitle.trim()) {
            setError('Please provide a ticket title');
            return;
        }
        setIsProcessing(true);
        setError(null);
        try {
            await processEmail(email.id, {
                title: ticketTitle,
                category_id: selectedCategory,
                subcategory_id: selectedSubcategory,
            });
            onActionComplete();
            onClose();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create ticket');
        } finally {
            setIsProcessing(false);
        }
    };

    // Handle add to pending (just close - already in pending, but refresh list)
    const handleAddToPending = () => {
        onActionComplete(); // Refresh the list
        onClose();
    };

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
        >
            <div
                className="bg-white dark:bg-surface-900 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl animate-fade-in border border-surface-200 dark:border-surface-700"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="p-5 border-b border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/50">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                            <div className="w-10 h-10 rounded-xl bg-primary-500/10 flex items-center justify-center shrink-0">
                                <Mail className="w-5 h-5 text-primary-600" />
                            </div>
                            <div>
                                <h2 className="text-lg font-bold text-surface-900 dark:text-white line-clamp-2">
                                    {email.subject || '(No Subject)'}
                                </h2>
                                <p className="text-sm text-surface-500 mt-1">
                                    Received: {formatDateIST(email.received_at)}
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 rounded-lg hover:bg-surface-200 dark:hover:bg-surface-700 transition-colors"
                        >
                            <X size={20} className="text-surface-500" />
                        </button>
                    </div>
                </div>

                {/* Sender Info */}
                <div className="px-5 py-3 border-b border-surface-200 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-800/30">
                    <div className="flex flex-wrap gap-x-6 gap-y-1 text-sm">
                        <div>
                            <span className="font-medium text-surface-600 dark:text-surface-400">From: </span>
                            <span className="text-surface-900 dark:text-white">{email.sender_name || 'Unknown'}</span>
                        </div>
                        <div>
                            <span className="font-medium text-surface-600 dark:text-surface-400">Email: </span>
                            <span className="text-primary-600 dark:text-primary-400">{email.sender_email}</span>
                        </div>
                    </div>
                </div>

                {/* Body */}
                <div className="p-5 overflow-auto max-h-[40vh] bg-white dark:bg-surface-900">
                    {email.body_html ? (
                        <div
                            className="prose dark:prose-invert max-w-none text-sm"
                            dangerouslySetInnerHTML={{ __html: email.body_html }}
                        />
                    ) : (
                        <pre className="whitespace-pre-wrap text-sm text-surface-700 dark:text-surface-300 font-sans">
                            {email.body_text || '(No content)'}
                        </pre>
                    )}
                </div>

                {/* Attachments */}
                {email.attachments && email.attachments.length > 0 && (
                    <div className="px-5 py-3 border-t border-surface-200 dark:border-surface-700 bg-surface-50/50 dark:bg-surface-800/30">
                        <div className="flex items-center gap-2 text-sm text-surface-600 dark:text-surface-400">
                            <Paperclip size={16} />
                            <span className="font-medium">{email.attachments.length} attachment(s):</span>
                            <div className="flex flex-wrap gap-2">
                                {email.attachments.map((att) => (
                                    <span key={att.id} className="px-2 py-0.5 rounded bg-surface-100 dark:bg-surface-800 text-xs">
                                        {att.file_name}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Error Message */}
                {error && (
                    <div className="px-5 py-2 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm">
                        {error}
                    </div>
                )}

                {/* Discard Prompt */}
                {showDiscardPrompt && (
                    <div className="px-5 py-4 border-t border-surface-200 dark:border-surface-700 bg-red-50/50 dark:bg-red-900/10">
                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                            Reason for discarding:
                        </label>
                        <textarea
                            value={discardReason}
                            onChange={(e) => setDiscardReason(e.target.value)}
                            placeholder="e.g., Spam, Duplicate, Not relevant..."
                            className="w-full p-3 border border-surface-300 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-800 text-sm resize-none"
                            rows={2}
                            autoFocus
                        />
                    </div>
                )}

                {/* Convert Form */}
                {showConvertForm && (
                    <div className="px-5 py-4 border-t border-surface-200 dark:border-surface-700 bg-green-50/50 dark:bg-green-900/10 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="block text-xs font-medium text-surface-600 dark:text-surface-400 mb-1">Category</label>
                                <select
                                    value={selectedCategory}
                                    onChange={(e) => handleCategoryChange(e.target.value)}
                                    className="w-full p-2 border border-surface-300 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-800 text-sm"
                                >
                                    <option value="">Select category...</option>
                                    {categories.map((cat) => (
                                        <option key={cat.id} value={cat.id}>{cat.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-xs font-medium text-surface-600 dark:text-surface-400 mb-1">Subcategory</label>
                                <select
                                    value={selectedSubcategory}
                                    onChange={(e) => setSelectedSubcategory(e.target.value)}
                                    className="w-full p-2 border border-surface-300 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-800 text-sm"
                                    disabled={!selectedCategory}
                                >
                                    <option value="">Select subcategory...</option>
                                    {subcategories.map((sub) => (
                                        <option key={sub.id} value={sub.id}>{sub.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-surface-600 dark:text-surface-400 mb-1">Ticket Title</label>
                            <input
                                type="text"
                                value={ticketTitle}
                                onChange={(e) => setTicketTitle(e.target.value)}
                                className="w-full p-2 border border-surface-300 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-800 text-sm"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-surface-600 dark:text-surface-400 mb-1">Description</label>
                            <textarea
                                value={ticketDescription}
                                onChange={(e) => setTicketDescription(e.target.value)}
                                className="w-full p-2 border border-surface-300 dark:border-surface-600 rounded-lg bg-white dark:bg-surface-800 text-sm resize-none"
                                rows={3}
                            />
                        </div>
                    </div>
                )}

                {/* Action Buttons */}
                <div className="p-5 border-t border-surface-200 dark:border-surface-700 bg-surface-50 dark:bg-surface-800/50">
                    <div className="flex items-center justify-between gap-3">
                        {/* Left: Cancel/Back */}
                        <button
                            onClick={() => {
                                if (showDiscardPrompt) setShowDiscardPrompt(false);
                                else if (showConvertForm) setShowConvertForm(false);
                                else onClose();
                            }}
                            className="px-4 py-2 text-sm font-medium text-surface-600 dark:text-surface-400 hover:bg-surface-100 dark:hover:bg-surface-700 rounded-lg transition-colors"
                            disabled={isProcessing}
                        >
                            {showDiscardPrompt || showConvertForm ? 'Back' : 'Cancel'}
                        </button>

                        {/* Right: Action Buttons */}
                        <div className="flex items-center gap-2">
                            {!showDiscardPrompt && !showConvertForm && (
                                <>
                                    {/* Discard Button */}
                                    <button
                                        onClick={() => setShowDiscardPrompt(true)}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                        disabled={isProcessing}
                                    >
                                        <Trash2 size={16} />
                                        Discard
                                    </button>

                                    {/* Add to Pending Button */}
                                    <button
                                        onClick={handleAddToPending}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-surface-700 dark:text-surface-300 bg-surface-100 dark:bg-surface-700 hover:bg-surface-200 dark:hover:bg-surface-600 rounded-lg transition-colors"
                                        disabled={isProcessing}
                                    >
                                        <Inbox size={16} />
                                        Add to Pending
                                    </button>

                                    {/* Convert to Ticket Button */}
                                    <button
                                        onClick={handleShowConvertForm}
                                        className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors"
                                        disabled={isProcessing}
                                    >
                                        <Ticket size={16} />
                                        Convert to Ticket
                                    </button>
                                </>
                            )}

                            {showDiscardPrompt && (
                                <button
                                    onClick={handleDiscard}
                                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors disabled:opacity-50"
                                    disabled={isProcessing || !discardReason.trim()}
                                >
                                    {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Trash2 size={16} />}
                                    Confirm Discard
                                </button>
                            )}

                            {showConvertForm && (
                                <button
                                    onClick={handleConvertToTicket}
                                    className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-primary-600 hover:bg-primary-700 rounded-lg transition-colors disabled:opacity-50"
                                    disabled={isProcessing || !selectedCategory || !selectedSubcategory || !ticketTitle.trim()}
                                >
                                    {isProcessing ? <Loader2 size={16} className="animate-spin" /> : <Ticket size={16} />}
                                    Create Ticket
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
