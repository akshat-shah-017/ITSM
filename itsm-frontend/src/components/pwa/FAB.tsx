// Components - PWA Floating Action Button
// A floating button for quick ticket creation on mobile

import { useState } from 'react';
import { Plus } from 'lucide-react';
import { QuickTicketModal } from './QuickTicketModal';

export function FAB() {
    const [isModalOpen, setIsModalOpen] = useState(false);

    return (
        <>
            {/* Floating Action Button - Hidden when modal is open */}
            {!isModalOpen && (
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="fab"
                    aria-label="Create new ticket"
                >
                    <Plus className="w-6 h-6" />
                </button>
            )}

            {/* Quick Ticket Modal */}
            {isModalOpen && (
                <QuickTicketModal onClose={() => setIsModalOpen(false)} />
            )}
        </>
    );
}
