// Components - Empty State

import React from 'react';

interface EmptyStateProps {
    /** Main message */
    message: string;
    /** Optional description */
    description?: string;
    /** Optional icon (emoji or component) */
    icon?: React.ReactNode;
    /** Optional action button */
    action?: {
        label: string;
        onClick: () => void;
    };
}

/**
 * Empty state component for when lists have no items
 */
export function EmptyState({ message, description, icon, action }: EmptyStateProps) {
    return (
        <div className="empty-state">
            {icon && <div className="empty-state-icon">{icon}</div>}
            <h3 className="empty-state-message">{message}</h3>
            {description && <p className="empty-state-description">{description}</p>}
            {action && (
                <button className="empty-state-action" onClick={action.onClick}>
                    {action.label}
                </button>
            )}
        </div>
    );
}
