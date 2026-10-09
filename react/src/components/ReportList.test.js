import { fireEvent, render, screen } from '@testing-library/react';
import React from 'react';
import ReportList from './ReportList';

const REPORTS = [
    {
        id: 1,
        file_full_name: 'picture.jpg',
        reporter_name: 'student',
        category: 'inapproprié',
        message: 'problème',
        created_at: '2026-10-08T12:00:00Z',
    },
    {
        id: 2,
        file_full_name: 'photo.jpg',
        reporter_name: 'other_student',
        category: 'qualité',
        message: '',
        created_at: '2026-10-08T13:00:00Z',
    },
];

describe('ReportList', () => {
    test('shows each report with file, reporter, category and message', () => {
        render(<ReportList reports={REPORTS} />);
        expect(screen.getByText('picture.jpg')).toBeInTheDocument();
        expect(screen.getByText('student')).toBeInTheDocument();
        // Le message est rendu dans « {message} » : le texte du node est
        // « problème » au complet, donc on matche par regex.
        expect(screen.getByText(/problème/)).toBeInTheDocument();
        expect(screen.getByText('photo.jpg')).toBeInTheDocument();
        expect(screen.getByText('other_student')).toBeInTheDocument();
        // Un signalement sans message n'affiche pas de citation vide.
        expect(screen.queryByText(/« »/)).not.toBeInTheDocument();
    });

    test('shows a friendly empty state', () => {
        render(<ReportList reports={[]} />);
        expect(screen.getByText('Aucun signalement sur cette galerie.')).toBeInTheDocument();
    });

    test('each report can be dismissed', () => {
        const onDismiss = jest.fn();
        render(<ReportList reports={REPORTS} onDismiss={onDismiss} />);
        const buttons = screen.getAllByRole('button', { name: 'Classer ce signalement' });
        expect(buttons).toHaveLength(2);
        fireEvent.click(buttons[1]);
        expect(onDismiss).toHaveBeenCalledWith(2);
    });

    test('no dismiss button when the list is read-only', () => {
        render(<ReportList reports={REPORTS} />);
        expect(screen.queryByRole('button', { name: 'Classer ce signalement' })).not.toBeInTheDocument();
    });
});
