import { useState, useCallback } from 'react';
import type { TicketDetail } from '../../types/ticket';
import type { ClosureCode, UpdatableStatus } from '../../types/mutations';
import { UPDATABLE_STATUSES, PRIORITY_VALUES } from '../../types/mutations';
import { useAuth } from '../../auth';
import { MutationForm, NoteInput, useMutationForm } from '../common/MutationForm';
import { ConfirmDialog, useConfirmDialog } from '../common/ConfirmDialog';
import {
    assignTicket,
    updateTicketStatus,
    closeTicket,
    updateTicketPriority,
    uploadAttachment,
    reassignTicket,
    getClosureCodes,
} from '../../api/mutations';
import { getManagerTeam } from '../../api/tickets';
import type { TeamMember } from '../../types/user';
import {
    UserPlus,
    RefreshCw,
    CheckCircle,
    AlertTriangle,
    Paperclip,
    ArrowRightLeft,
    Shield
} from 'lucide-react';

interface TicketActionsProps {
    ticket: TicketDetail;
    onTicketUpdate: () => Promise<void>;
}

export function TicketActions({ ticket, onTicketUpdate }: TicketActionsProps) {
    const { user, isEmployee, isManager } = useAuth();
    const isAssignedToMe = ticket.assigned_to?.id === user?.id;

    const canSelfAssign = isEmployee && !ticket.assigned_to && !ticket.is_closed;
    const canUpdateStatus = isEmployee && isAssignedToMe && !ticket.is_closed;
    const canClose = isEmployee && isAssignedToMe && !ticket.is_closed;
    const canUpdatePriority = isEmployee && (isAssignedToMe || isManager) && !ticket.is_closed;
    const canUploadAttachment = isEmployee && !ticket.is_closed;
    const canReassign = isManager && ticket.assigned_to && !ticket.is_closed;

    if (!canSelfAssign && !canUpdateStatus && !canClose && !canUpdatePriority && !canUploadAttachment && !canReassign) {
        return null;
    }

    return (
        <div className="card border-l-4 border-l-primary-500">
            <h3 className="text-sm font-bold uppercase tracking-wider text-surface-400 mb-4 flex items-center gap-2">
                <Shield className="w-4 h-4" />
                Actions
            </h3>

            {ticket.is_closed && (
                <div className="p-3 bg-surface-100 dark:bg-surface-800 rounded text-sm text-surface-500 text-center italic">
                    Ticket closed. Read-only mode.
                </div>
            )}

            <div className="grid grid-cols-1 gap-2">
                {canSelfAssign && <AssignToMeButton ticket={ticket} onSuccess={onTicketUpdate} />}
                {canUpdateStatus && <UpdateStatusButton ticket={ticket} onSuccess={onTicketUpdate} />}
                {canUploadAttachment && <UploadAttachmentButton ticket={ticket} onSuccess={onTicketUpdate} />}
                {canUpdatePriority && <UpdatePriorityButton ticket={ticket} onSuccess={onTicketUpdate} />}
                {canReassign && <ReassignButton ticket={ticket} onSuccess={onTicketUpdate} />}

                {canClose && (
                    <>
                        <div className="h-px bg-surface-100 dark:bg-surface-800 my-2" />
                        <CloseTicketButton ticket={ticket} onSuccess={onTicketUpdate} />
                    </>
                )}
            </div>
        </div>
    );
}

// ... (Sub-components follow with updated styling)

function AssignToMeButton({ ticket, onSuccess }: { ticket: TicketDetail; onSuccess: () => Promise<void>; }) {
    const dialog = useConfirmDialog();

    const handleConfirm = async () => {
        dialog.setIsLoading(true);
        try {
            await assignTicket(ticket.id);
            dialog.close();
            await onSuccess();
        } catch (error) {
            console.error('Failed to assign ticket:', error);
            dialog.close();
            await onSuccess();
        } finally {
            dialog.setIsLoading(false);
        }
    };

    return (
        <>
            <button className="btn btn-primary w-full justify-start" onClick={dialog.open}>
                <UserPlus className="w-4 h-4 mr-2" />
                Assign to Me
            </button>

            <ConfirmDialog
                isOpen={dialog.isOpen}
                isLoading={dialog.isLoading}
                title="Assign Ticket"
                message={`Are you sure you want to assign ticket ${ticket.ticket_number} to yourself?`}
                confirmText="Assign to Me"
                onConfirm={handleConfirm}
                onCancel={dialog.close}
            />
        </>
    );
}

function UpdateStatusButton({ ticket, onSuccess }: { ticket: TicketDetail; onSuccess: () => Promise<void>; }) {
    const form = useMutationForm();
    const [status, setStatus] = useState<UpdatableStatus>('In Progress');
    const [note, setNote] = useState('');
    const availableStatuses = UPDATABLE_STATUSES.filter(s => s !== ticket.status);
    const isValid = note.trim().length > 0;

    const handleSubmit = async () => {
        form.setIsSubmitting(true);
        form.setError(null);
        try {
            await updateTicketStatus(ticket.id, status, note);
            form.close();
            setNote('');
            await onSuccess();
        } catch (error) {
            form.setError(error);
        } finally {
            form.setIsSubmitting(false);
        }
    };

    const handleOpen = () => {
        setNote('');
        setStatus(availableStatuses[0] || 'In Progress');
        form.open();
    };

    return (
        <>
            <button className="btn btn-secondary w-full justify-start" onClick={handleOpen}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Update Status
            </button>

            <MutationForm
                isOpen={form.isOpen}
                title="Update Ticket Status"
                isSubmitting={form.isSubmitting}
                error={form.error}
                submitText="Update Status"
                isValid={isValid}
                onCancel={form.close}
                onSubmit={handleSubmit}
            >
                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-surface-700 dark:text-surface-300">New Status</label>
                    <select
                        className="input"
                        value={status}
                        onChange={(e) => setStatus(e.target.value as UpdatableStatus)}
                        disabled={form.isSubmitting}
                    >
                        {availableStatuses.map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                </div>
                <NoteInput value={note} onChange={setNote} placeholder="Reason for status change..." />
            </MutationForm>
        </>
    );
}

function CloseTicketButton({ ticket, onSuccess }: { ticket: TicketDetail; onSuccess: () => Promise<void>; }) {
    const form = useMutationForm();
    const [closureCodes, setClosureCodes] = useState<ClosureCode[]>([]);
    const [closureCodeId, setClosureCodeId] = useState('');
    const [note, setNote] = useState('');
    const [loadingCodes, setLoadingCodes] = useState(false);

    const loadClosureCodes = useCallback(async () => {
        setLoadingCodes(true);
        try {
            const codes = await getClosureCodes();
            // Backend already filters by is_active=True, so we use all returned codes
            setClosureCodes(codes);
            if (codes.length > 0) setClosureCodeId(codes[0].id);
        } catch (error) {
            form.setError(error);
        } finally {
            setLoadingCodes(false);
        }
    }, [form]);

    const isValid = closureCodeId.length > 0 && note.trim().length > 0;

    const handleSubmit = async () => {
        form.setIsSubmitting(true);
        form.setError(null);
        try {
            await closeTicket(ticket.id, closureCodeId, note);
            form.close();
            setNote('');
            await onSuccess();
        } catch (error) {
            form.setError(error);
        } finally {
            form.setIsSubmitting(false);
        }
    };

    const handleOpen = () => {
        setNote('');
        form.open();
        loadClosureCodes();
    };

    return (
        <>
            <button className="btn btn-danger w-full justify-start text-left" onClick={handleOpen}>
                <CheckCircle className="w-4 h-4 mr-2" />
                Close Ticket
            </button>

            <MutationForm
                isOpen={form.isOpen}
                title="Close Ticket"
                isSubmitting={form.isSubmitting}
                error={form.error}
                submitText="Close Ticket"
                isDangerous
                isValid={isValid}
                onCancel={form.close}
                onSubmit={handleSubmit}
            >
                {loadingCodes ? (
                    <p className="text-sm text-surface-500">Loading closure codes...</p>
                ) : (
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-surface-700 dark:text-surface-300">Closure Code</label>
                        <select
                            className="input"
                            value={closureCodeId}
                            onChange={(e) => setClosureCodeId(e.target.value)}
                            disabled={form.isSubmitting}
                        >
                            {closureCodes.map((code) => (
                                <option key={code.id} value={code.id}>
                                    {code.code} - {code.description}
                                </option>
                            ))}
                        </select>
                    </div>
                )}
                <NoteInput value={note} onChange={setNote} label="Resolution Details" placeholder="Describe how the ticket was resolved..." />
            </MutationForm>
        </>
    );
}

function UpdatePriorityButton({ ticket, onSuccess }: { ticket: TicketDetail; onSuccess: () => Promise<void>; }) {
    const form = useMutationForm();
    const [priority, setPriority] = useState<number>(ticket.priority || 3);
    const [note, setNote] = useState('');
    const priorityLabels: Record<number, string> = { 1: 'P1 - Critical', 2: 'P2 - High', 3: 'P3 - Medium', 4: 'P4 - Low' };
    const isValid = note.trim().length > 0;

    const handleSubmit = async () => {
        form.setIsSubmitting(true);
        form.setError(null);
        try {
            await updateTicketPriority(ticket.id, priority, note);
            form.close();
            setNote('');
            await onSuccess();
        } catch (error) {
            form.setError(error);
        } finally {
            form.setIsSubmitting(false);
        }
    };

    const handleOpen = () => {
        setNote('');
        setPriority(ticket.priority || 3);
        form.open();
    };

    return (
        <>
            <button className="btn btn-secondary w-full justify-start" onClick={handleOpen}>
                <AlertTriangle className="w-4 h-4 mr-2" />
                Set Priority
            </button>

            <MutationForm
                isOpen={form.isOpen}
                title="Update Priority"
                isSubmitting={form.isSubmitting}
                error={form.error}
                submitText="Update Priority"
                isValid={isValid}
                onCancel={form.close}
                onSubmit={handleSubmit}
            >
                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-surface-700 dark:text-surface-300">Priority Level</label>
                    <select
                        className="input"
                        value={priority}
                        onChange={(e) => setPriority(Number(e.target.value))}
                        disabled={form.isSubmitting}
                    >
                        {PRIORITY_VALUES.map((p) => <option key={p} value={p}>{priorityLabels[p]}</option>)}
                    </select>
                </div>
                <NoteInput value={note} onChange={setNote} placeholder="Reason for priority change..." />
            </MutationForm>
        </>
    );
}

function UploadAttachmentButton({ ticket, onSuccess }: { ticket: TicketDetail; onSuccess: () => Promise<void>; }) {
    const form = useMutationForm();
    const [file, setFile] = useState<File | null>(null);
    const canUpload = ticket.attachments.length < 5;
    const isValid = file !== null;

    const handleSubmit = async () => {
        if (!file) return;
        form.setIsSubmitting(true);
        form.setError(null);
        try {
            await uploadAttachment(ticket.id, file);
            form.close();
            setFile(null);
            await onSuccess();
        } catch (error) {
            form.setError(error);
        } finally {
            form.setIsSubmitting(false);
        }
    };

    if (!canUpload) return <button className="btn btn-secondary w-full justify-start opacity-50 cursor-not-allowed" disabled>Max Attachments Reached</button>;

    return (
        <>
            <button className="btn btn-secondary w-full justify-start" onClick={form.open}>
                <Paperclip className="w-4 h-4 mr-2" />
                Add Attachment
            </button>

            <MutationForm
                isOpen={form.isOpen}
                title="Upload Attachment"
                isSubmitting={form.isSubmitting}
                error={form.error}
                submitText="Upload"
                isValid={isValid}
                onCancel={form.close}
                onSubmit={handleSubmit}
            >
                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-surface-700 dark:text-surface-300">File</label>
                    <input
                        type="file"
                        className="block w-full text-sm text-surface-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 dark:file:bg-primary-900/20 dark:file:text-primary-400"
                        onChange={(e) => {
                            const f = e.target.files?.[0];
                            if (f && f.size > 25 * 1024 * 1024) {
                                form.setError({ response: { data: { error: { code: 'FILE_TOO_LARGE', message: 'File too large' } } } });
                                return;
                            }
                            setFile(f || null);
                        }}
                        disabled={form.isSubmitting}
                    />
                    <p className="text-xs text-surface-400">Max size: 25MB</p>
                </div>
            </MutationForm>
        </>
    );
}

function ReassignButton({ ticket, onSuccess }: { ticket: TicketDetail; onSuccess: () => Promise<void>; }) {
    const form = useMutationForm();
    const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
    const [assignedTo, setAssignedTo] = useState('');
    const [note, setNote] = useState('');
    const [loadingTeam, setLoadingTeam] = useState(false);

    const loadTeamMembers = useCallback(async () => {
        setLoadingTeam(true);
        try {
            const members = await getManagerTeam();
            const filtered = members.filter(m => m.id !== ticket.assigned_to?.id);
            setTeamMembers(filtered);
            if (filtered.length > 0) setAssignedTo(filtered[0].id);
        } catch (error) {
            form.setError(error);
        } finally {
            setLoadingTeam(false);
        }
    }, [ticket.assigned_to?.id, form]);

    const isValid = assignedTo.length > 0 && note.trim().length > 0;

    const handleSubmit = async () => {
        form.setIsSubmitting(true);
        form.setError(null);
        try {
            await reassignTicket(ticket.id, assignedTo, note);
            form.close();
            setNote('');
            await onSuccess();
        } catch (error) {
            form.setError(error);
        } finally {
            form.setIsSubmitting(false);
        }
    };

    const handleOpen = () => {
        setNote('');
        form.open();
        loadTeamMembers();
    };

    return (
        <>
            <button className="btn btn-secondary w-full justify-start" onClick={handleOpen}>
                <ArrowRightLeft className="w-4 h-4 mr-2" />
                Reassign
            </button>

            <MutationForm
                isOpen={form.isOpen}
                title="Reassign Ticket"
                isSubmitting={form.isSubmitting}
                error={form.error}
                submitText="Reassign"
                isValid={isValid}
                onCancel={form.close}
                onSubmit={handleSubmit}
            >
                {loadingTeam ? <p>Loading team...</p> : (
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-surface-700 dark:text-surface-300">Assign To</label>
                        <select className="input" value={assignedTo} onChange={(e) => setAssignedTo(e.target.value)} disabled={form.isSubmitting}>
                            {teamMembers.map((m) => <option key={m.id} value={m.id}>{m.name}</option>)}
                        </select>
                    </div>
                )}
                <NoteInput value={note} onChange={setNote} placeholder="Reason for reassignment..." />
            </MutationForm>
        </>
    );
}
