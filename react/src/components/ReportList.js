import React from 'react';
import 'bootstrap/dist/css/bootstrap.min.css';
import Button from 'react-bootstrap/Button';
import ListGroup from 'react-bootstrap/ListGroup';

export default function ReportList({ reports, onDismiss }) {
    if (!reports || reports.length === 0) {
        return <p>Aucun signalement sur cette galerie.</p>;
    }
    return (
        <ListGroup>
            {reports.map((r) => (
                <ListGroup.Item key={r.id}>
                    <strong>{r.file_full_name}</strong>
                    {' '}signalée par <strong>{r.reporter_name}</strong>
                    {' '}le {new Date(r.created_at).toLocaleString('fr-FR')} — {r.category}
                    {r.message && <div>« {r.message} »</div>}
                    {onDismiss && (
                        <div className="mt-2">
                            <Button variant="outline-secondary" size="sm" onClick={() => onDismiss(r.id)}>
                                Classer ce signalement
                            </Button>
                        </div>
                    )}
                </ListGroup.Item>
            ))}
        </ListGroup>
    );
}
