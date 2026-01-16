import React, { useState, useEffect } from 'react';

const AddGradeModal = ({ isOpen, onClose, onSave, subjects }) => {
    const [value, setValue] = useState('');
    const [subjectId, setSubjectId] = useState('');
    const [type, setType] = useState('Schulprüfung'); // Default to a safe valid value

    // Helper to get options based on subject
    const getTypeOptions = (sId) => {
        const selectedSubject = subjects.find(s => s.id === parseInt(sId));
        if (!selectedSubject) return [];

        if (selectedSubject.name === "Mathematik") {
            return [
                { value: "Schulprüfung", label: "Schulprüfung" },
                { value: "Gymiprüfung", label: "Gymiprüfung" }
            ];
        } else if (selectedSubject.name === "Deutsch") {
            return [
                { value: "Schulprüfung", label: "Schulprüfung" },
                { value: "Aufsatz", label: "Aufsatz (Gymiprüfung)" },
                { value: "Sprachbetrachtung", label: "Sprachbetrachtung (Gymiprüfung)" }
            ];
        } else {
            return [
                { value: "Schulprüfung", label: "Schulprüfung" },
                { value: "Gymiprüfung", label: "Gymiprüfung" }
            ];
        }
    };

    // Reset form when opening
    useEffect(() => {
        if (isOpen && subjects.length > 0) {
            setValue('');
            const firstSubjectId = subjects[0].id;
            setSubjectId(firstSubjectId);
            const options = getTypeOptions(firstSubjectId);
            if (options.length > 0) setType(options[0].value);
        }
    }, [isOpen, subjects]);

    // Update type when subject changes
    useEffect(() => {
        if (subjectId) {
            const options = getTypeOptions(subjectId);
            // Only reset if current type is not valid for new subject? 
            // Or always reset to be safe? 
            // Better to default to Vornote (usually first) or keep if it exists.
            const isValid = options.find(o => o.value === type);
            if (!isValid && options.length > 0) {
                setType(options[0].value);
            }
        }
    }, [subjectId]);

    if (!isOpen) return null;

    const handleSubmit = (e) => {
        e.preventDefault();
        onSave({
            value: parseFloat(value),
            subject_id: parseInt(subjectId),
            type: type
        });
        onClose();
    };

    const typeOptions = getTypeOptions(subjectId);

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center',
            zIndex: 1000
        }}>
            <div style={{
                background: 'white', padding: '2rem', borderRadius: '12px', width: '90%', maxWidth: '400px',
                boxShadow: '0 20px 25px -5px rgb(0 0 0 / 0.1)'
            }}>
                <h3 style={{ marginTop: 0 }}>Note eintragen</h3>
                <form onSubmit={handleSubmit}>
                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Fach</label>
                        <select
                            style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #ccc' }}
                            value={subjectId}
                            onChange={e => setSubjectId(e.target.value)}
                            required
                        >
                            {subjects.map(s => (
                                <option key={s.id} value={s.id}>{s.name}</option>
                            ))}
                        </select>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Typ</label>
                        <select
                            style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #ccc' }}
                            value={type}
                            onChange={e => setType(e.target.value)}
                        >
                            {typeOptions.map(o => (
                                <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                        </select>
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Note</label>
                        <input
                            type="number" step="0.1" min="1" max="6"
                            style={{ width: '100%', padding: '8px', borderRadius: '6px', border: '1px solid #ccc' }}
                            value={value}
                            onChange={e => setValue(e.target.value)}
                            placeholder="z.B. 4.5"
                            required
                        />
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                        <button type="button" onClick={onClose} className="btn" style={{ background: '#f1f5f9' }}>
                            Abbrechen
                        </button>
                        <button type="submit" className="btn btn-primary">
                            Speichern
                        </button>
                    </div>
                </form>
            </div>
        </div >
    );
};

export default AddGradeModal;
