/**
 * EmailInboxPage - Employee Email Intake
 * Allows employees to upload emails and convert them to tickets
 */
import { useState, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Mail, ArrowLeft, Inbox, Check, X, Eye, ArrowUp, ArrowDown } from 'lucide-react';
import { EmailDropZone, EmailPreviewModal } from '../../components/email';
import { LoadingSpinner, ErrorMessage, EmptyState, Pagination } from '../../components/common';
import { ingestEmail, getPendingEmails, type EmailIngest } from '../../api/email';
import { formatDateIST } from '../../utils/dateFormat';

export function EmailInboxPage() {
    const [pendingEmails, setPendingEmails] = useState<EmailIngest[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const [page, setPage] = useState(1);
    const [totalCount, setTotalCount] = useState(0);
    const [selectedEmail, setSelectedEmail] = useState<EmailIngest | null>(null);
    const [loadError, setLoadError] = useState<Error | null>(null);
    const [sortOrder, setSortOrder] = useState<'newest' | 'oldest'>('newest');

    // Load pending emails
    const loadEmails = useCallback(async () => {
        setIsLoading(true);
        setLoadError(null);
        try {
            const response = await getPendingEmails({ page, page_size: 10 });
            setPendingEmails(response.results);
            setTotalCount(response.total_count);
        } catch (err) {
            setLoadError(err instanceof Error ? err : new Error('Failed to load emails'));
        } finally {
            setIsLoading(false);
        }
    }, [page]);

    // Initial load
    useEffect(() => {
        loadEmails();
    }, [loadEmails]);

    // Handle file upload - AUTO-POPUP on successful ingest
    const handleFileUpload = useCallback(async (file: File) => {
        setUploadError(null);
        setIsUploading(true);
        try {
            const ingestedEmail = await ingestEmail(file);
            // AUTO-POPUP: Show the preview modal immediately
            setSelectedEmail(ingestedEmail);
            await loadEmails(); // Refresh list in background
        } catch (err) {
            setUploadError(err instanceof Error ? err.message : 'Failed to upload email');
        } finally {
            setIsUploading(false);
        }
    }, [loadEmails]);

    // Handle email selection for preview
    const handlePreview = (email: EmailIngest) => {
        setSelectedEmail(email);
    };

    // Handle close preview
    const handleClosePreview = () => {
        setSelectedEmail(null);
    };

    // Handle action complete (refresh list)
    const handleActionComplete = () => {
        loadEmails();
    };

    // Toggle sort order
    const toggleSort = () => {
        setSortOrder(prev => prev === 'newest' ? 'oldest' : 'newest');
    };

    // Sort emails by received_at
    const sortedEmails = [...pendingEmails].sort((a, b) => {
        const dateA = new Date(a.received_at).getTime();
        const dateB = new Date(b.received_at).getTime();
        return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
    });

    return (
        <div className="space-y-6">
            {/* Header */}
            <header className="flex items-center gap-4">
                <Link
                    to="/employee/queue"
                    className="p-2 rounded-lg text-surface-500 hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
                >
                    <ArrowLeft size={20} />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-surface-900 dark:text-white flex items-center gap-2">
                        <Mail className="text-primary-500" />
                        Email Inbox
                    </h1>
                    <p className="text-surface-500 text-sm">
                        Drag and drop email files to create tickets
                    </p>
                </div>
            </header>

            {/* Drop Zone */}
            <EmailDropZone
                onFileUpload={handleFileUpload}
                isLoading={isUploading}
                error={uploadError}
            />

            {/* Pending Emails Section */}
            <section className="glass-panel p-6 rounded-2xl">
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-semibold text-surface-900 dark:text-white flex items-center gap-2">
                        <Inbox size={20} className="text-surface-400" />
                        Pending Emails
                        <span className="text-xs font-normal text-surface-500 px-2 py-0.5 rounded-full bg-surface-100 dark:bg-surface-800">
                            {totalCount}
                        </span>
                    </h2>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={toggleSort}
                            className="flex items-center gap-1 text-sm text-surface-600 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors px-2 py-1 rounded bg-surface-100 dark:bg-surface-800"
                            title={`Sort by ${sortOrder === 'newest' ? 'oldest first' : 'newest first'}`}
                        >
                            {sortOrder === 'newest' ? <ArrowDown size={14} /> : <ArrowUp size={14} />}
                            {sortOrder === 'newest' ? 'Newest' : 'Oldest'}
                        </button>
                        <button
                            onClick={loadEmails}
                            className="text-sm text-primary-600 hover:text-primary-700 transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {isLoading && pendingEmails.length === 0 && (
                    <LoadingSpinner message="Loading emails..." />
                )}

                {loadError && (
                    <ErrorMessage
                        error={loadError}
                        title="Failed to load emails"
                        onRetry={loadEmails}
                    />
                )}

                {!isLoading && !loadError && pendingEmails.length === 0 && (
                    <EmptyState
                        icon="mail"
                        message="No pending emails"
                        description="Upload an email file to get started"
                    />
                )}

                {pendingEmails.length > 0 && (
                    <div className="space-y-3">
                        {sortedEmails.map((email) => (
                            <div
                                key={email.id}
                                className="p-4 rounded-xl border border-surface-200 dark:border-surface-700 bg-white dark:bg-surface-900 hover:border-primary-300 dark:hover:border-primary-700 transition-colors cursor-pointer"
                                onClick={() => handlePreview(email)}
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <h3 className="font-medium text-surface-900 dark:text-white truncate">
                                            {email.subject || '(No Subject)'}
                                        </h3>
                                        <p className="text-sm text-surface-500 mt-1">
                                            From: {email.sender_name || email.sender_email}
                                        </p>
                                        <p className="text-xs text-surface-400 mt-1">
                                            Received: {formatDateIST(email.received_at)}
                                        </p>
                                    </div>
                                    <div className="flex items-center gap-2 shrink-0">
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handlePreview(email); }}
                                            className="p-2 rounded-lg text-surface-600 hover:text-primary-600 hover:bg-primary-50 dark:hover:bg-primary-900/20 transition-colors"
                                            title="Preview"
                                        >
                                            <Eye size={18} />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handlePreview(email); }}
                                            className="p-2 rounded-lg text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 transition-colors"
                                            title="Create Ticket"
                                        >
                                            <Check size={18} />
                                        </button>
                                        <button
                                            onClick={(e) => { e.stopPropagation(); handlePreview(email); }}
                                            className="p-2 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                            title="Discard"
                                        >
                                            <X size={18} />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}

                        <Pagination
                            page={page}
                            pageSize={10}
                            totalCount={totalCount}
                            onPageChange={setPage}
                        />
                    </div>
                )}
            </section>

            {/* Email Preview Modal - Uses new component */}
            {selectedEmail && (
                <EmailPreviewModal
                    email={selectedEmail}
                    onClose={handleClosePreview}
                    onActionComplete={handleActionComplete}
                />
            )}
        </div>
    );
}
